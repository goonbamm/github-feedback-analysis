"""Utility helpers for interacting with Large Language Model endpoints."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List

import requests

from .models import PullRequestReviewBundle, ReviewPoint, ReviewSummary
from .utils import limit_items, truncate_patch

logger = logging.getLogger(__name__)


MAX_FILES_IN_PROMPT = 10
MAX_FILES_WITH_PATCH_SNIPPETS = 5
MAX_PATCH_LINES_PER_FILE = 20


@dataclass(slots=True)
class LLMClient:
    """Minimal HTTP client for chat-completion style LLM APIs."""

    endpoint: str
    model: str = ""
    timeout: int = 60

    def _build_messages(self, bundle: PullRequestReviewBundle) -> List[Dict[str, str]]:
        """Create the prompt messages describing the pull request."""

        summary_lines = [
            f"저장소: {bundle.repo}",
            f"Pull Request: #{bundle.number} {bundle.title}",
            f"작성자: {bundle.author or 'unknown'}",
            f"변경 통계: +{bundle.additions} / -{bundle.deletions} ({bundle.changed_files}개 파일)",
            "",
            "Pull Request 본문:",
            bundle.body or "<비어있음>",
            "",
        ]

        if bundle.review_bodies:
            summary_lines.append("기존 리뷰:")
            summary_lines.extend(f"- {body}" for body in bundle.review_bodies)
            summary_lines.append("")

        if bundle.review_comments:
            summary_lines.append("인라인 리뷰 코멘트:")
            summary_lines.extend(f"- {comment}" for comment in bundle.review_comments[:20])
            summary_lines.append("")

        summary_lines.append("변경된 파일:")
        for index, file in enumerate(limit_items(bundle.files, MAX_FILES_IN_PROMPT)):
            summary_lines.append(
                f"- {file.filename} ({file.status}, +{file.additions}/-{file.deletions}, 변경={file.changes})"
            )
            if (
                index < MAX_FILES_WITH_PATCH_SNIPPETS
                and file.patch
                and (snippet := truncate_patch(file.patch, MAX_PATCH_LINES_PER_FILE))
            ):
                summary_lines.append("```diff")
                summary_lines.append(snippet)
                summary_lines.append("```")
        summary_lines.append("")

        prompt = "\n".join(summary_lines)

        return [
            {
                "role": "system",
                "content": (
                    "당신은 경험이 풍부한 소프트웨어 리뷰어입니다. 구체적인 장점과 개선 기회를 강조하며 균형 잡히고 실행 가능한 "
                    "피드백을 제공하세요. 반드시 JSON 형식으로 응답하며, 다음 키를 포함해야 합니다: overview, strengths, improvements. "
                    "각 strengths/improvements 항목은 message와 example을 포함해야 합니다. 모든 응답은 한국어로 작성하세요."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ]

    def _parse_points(self, payload: Iterable[Any]) -> List[ReviewPoint]:
        """Normalise payload entries into :class:`ReviewPoint` objects."""

        points: List[ReviewPoint] = []
        for item in payload:
            if isinstance(item, dict):
                message = str(item.get("message") or item.get("summary") or "").strip()
                example_raw = item.get("example") or item.get("detail")
                example = str(example_raw).strip() if example_raw else None
            else:
                message = str(item).strip()
                example = None
            if message:
                points.append(ReviewPoint(message=message, example=example or None))
        return points

    def _parse_response(self, response_payload: Dict[str, Any]) -> ReviewSummary:
        """Extract the JSON content from the LLM response."""

        choices = response_payload.get("choices") or []
        if not choices:
            raise ValueError("LLM response did not contain choices")

        message = choices[0].get("message") or {}
        content = message.get("content") or ""

        try:
            raw = json.loads(content)
        except json.JSONDecodeError as exc:  # pragma: no cover - defensive fallback
            raise ValueError("LLM response was not valid JSON") from exc

        overview = str(raw.get("overview", "")).strip()
        strengths = self._parse_points(raw.get("strengths", []))
        improvements = self._parse_points(raw.get("improvements", []))

        return ReviewSummary(overview=overview, strengths=strengths, improvements=improvements)

    def generate_review(self, bundle: PullRequestReviewBundle) -> ReviewSummary:
        """Invoke the configured LLM endpoint and parse the structured feedback."""

        base_payload = {
            "model": self.model or "default-model",
            "messages": self._build_messages(bundle),
            "temperature": 0.2,
        }

        request_payloads: List[Dict[str, Any]] = [
            base_payload | {"response_format": {"type": "json_object"}}
        ]
        request_payloads.append(base_payload)

        last_error: Exception | None = None
        for request_payload in request_payloads:
            try:
                response = requests.post(
                    self.endpoint,
                    json=request_payload,
                    timeout=self.timeout,
                )
                response.raise_for_status()
                try:
                    response_payload = response.json()
                except ValueError as exc:  # pragma: no cover - upstream bug/HTML error page
                    last_error = ValueError("LLM response was not valid JSON")
                    if "response_format" in request_payload:
                        continue
                    raise last_error from exc

                try:
                    return self._parse_response(response_payload)
                except ValueError as exc:
                    last_error = exc
                    if "response_format" in request_payload:
                        continue
                    raise
            except requests.HTTPError as exc:
                error_text = ""
                if exc.response is not None:
                    try:
                        error_text = exc.response.text
                    except Exception:  # pragma: no cover - defensive guard for rare encodings
                        error_text = ""

                last_error = exc
                status_code = exc.response.status_code if exc.response is not None else None
                error_text_lower = error_text.lower()

                if "response_format" in request_payload:
                    if status_code is not None and status_code >= 500:
                        continue
                    if status_code in {400, 404, 415, 422} and (
                        "json_object" in error_text_lower or "response_format" in error_text_lower
                    ):
                        continue
                raise
            except Exception as exc:  # pragma: no cover - network failures already handled elsewhere
                last_error = exc
                break

        if last_error is not None:
            raise last_error

        raise RuntimeError("LLM request failed without raising an explicit error")

    def complete(
        self,
        messages: List[Dict[str, str]],
        *,
        temperature: float = 0.3,
    ) -> str:
        """Execute a generic chat completion request and return the content."""

        payload = {
            "model": self.model or "default-model",
            "messages": messages,
            "temperature": temperature,
        }

        response = requests.post(
            self.endpoint,
            json=payload,
            timeout=self.timeout,
        )
        response.raise_for_status()

        try:
            response_payload = response.json()
        except ValueError as exc:  # pragma: no cover - upstream bug/HTML error page
            raise ValueError("LLM response was not valid JSON") from exc

        choices = response_payload.get("choices") or []
        if not choices:
            raise ValueError("LLM response did not contain choices")

        message = choices[0].get("message") or {}
        content = str(message.get("content") or "").strip()
        if not content:
            raise ValueError("LLM response did not contain content")

        return content

    def analyze_commit_messages(
        self, commits: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """Analyze commit message quality using LLM."""
        if not commits:
            return {
                "good_messages": 0,
                "poor_messages": 0,
                "suggestions": ["커밋 메시지를 분석할 데이터가 없습니다."],
                "examples_good": [],
                "examples_poor": [],
            }

        # Sample commits for analysis (limit to 50)
        sample_commits = commits[:50]

        commit_list = "\n".join([
            f"{i+1}. {commit['message'][:100]} (SHA: {commit['sha'][:7]})"
            for i, commit in enumerate(sample_commits)
        ])

        messages = [
            {
                "role": "system",
                "content": (
                    "당신은 코드 리뷰 전문가입니다. 커밋 메시지의 품질을 평가하세요. "
                    "좋은 커밋 메시지는 명확하고, 간결하며, 변경 사항의 이유를 설명합니다. "
                    "반드시 JSON 형식으로 응답하며, 다음 키를 포함해야 합니다: "
                    "good_count (좋은 메시지 수), poor_count (개선이 필요한 메시지 수), "
                    "suggestions (개선 제안 목록), examples_good (좋은 예시 최대 3개), "
                    "examples_poor (개선이 필요한 예시 최대 3개). 모든 응답은 한국어로 작성하세요."
                ),
            },
            {
                "role": "user",
                "content": f"다음 커밋 메시지들을 분석해주세요:\n\n{commit_list}",
            },
        ]

        try:
            response = self.complete(messages, temperature=0.2)
            result = json.loads(response)

            return {
                "good_messages": result.get("good_count", 0),
                "poor_messages": result.get("poor_count", 0),
                "suggestions": result.get("suggestions", []),
                "examples_good": result.get("examples_good", []),
                "examples_poor": result.get("examples_poor", []),
            }
        except (ValueError, requests.RequestException, json.JSONDecodeError) as exc:
            # Fallback to simple heuristics on known errors
            logger.warning(f"LLM commit analysis failed: {exc}")
            return self._fallback_commit_analysis(sample_commits)

    def analyze_pr_titles(self, pr_titles: List[Dict[str, str]]) -> Dict[str, Any]:
        """Analyze pull request title quality using LLM."""
        if not pr_titles:
            return {
                "clear_titles": 0,
                "vague_titles": 0,
                "suggestions": ["PR 제목을 분석할 데이터가 없습니다."],
                "examples_good": [],
                "examples_poor": [],
            }

        # Sample PR titles for analysis (limit to 50)
        sample_prs = pr_titles[:50]

        pr_list = "\n".join([
            f"{i+1}. #{pr['number']}: {pr['title']}"
            for i, pr in enumerate(sample_prs)
        ])

        messages = [
            {
                "role": "system",
                "content": (
                    "당신은 코드 리뷰 전문가입니다. Pull Request 제목의 품질을 평가하세요. "
                    "좋은 PR 제목은 변경 사항을 명확하게 설명하고, 간결하며, 이해하기 쉽습니다. "
                    "반드시 JSON 형식으로 응답하며, 다음 키를 포함해야 합니다: "
                    "clear_count (명확한 제목 수), vague_count (모호한 제목 수), "
                    "suggestions (개선 제안 목록), examples_good (좋은 예시 최대 3개), "
                    "examples_poor (개선이 필요한 예시 최대 3개). 모든 응답은 한국어로 작성하세요."
                ),
            },
            {
                "role": "user",
                "content": f"다음 PR 제목들을 분석해주세요:\n\n{pr_list}",
            },
        ]

        try:
            response = self.complete(messages, temperature=0.2)
            result = json.loads(response)

            return {
                "clear_titles": result.get("clear_count", 0),
                "vague_titles": result.get("vague_count", 0),
                "suggestions": result.get("suggestions", []),
                "examples_good": result.get("examples_good", []),
                "examples_poor": result.get("examples_poor", []),
            }
        except (ValueError, requests.RequestException, json.JSONDecodeError) as exc:
            # Fallback to simple heuristics on known errors
            logger.warning(f"LLM PR title analysis failed: {exc}")
            return self._fallback_pr_title_analysis(sample_prs)

    def analyze_review_tone(
        self, review_comments: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """Analyze code review tone and style using LLM."""
        if not review_comments:
            return {
                "constructive_reviews": 0,
                "harsh_reviews": 0,
                "neutral_reviews": 0,
                "suggestions": ["리뷰 코멘트를 분석할 데이터가 없습니다."],
                "examples_good": [],
                "examples_improve": [],
            }

        # Sample review comments (limit to 30)
        sample_reviews = review_comments[:30]

        review_list = "\n".join([
            f"{i+1}. (PR #{review['pr_number']}, {review['author']}): {review['body'][:200]}"
            for i, review in enumerate(sample_reviews)
        ])

        messages = [
            {
                "role": "system",
                "content": (
                    "당신은 팀 협업 전문가입니다. 코드 리뷰 코멘트의 톤과 스타일을 평가하세요. "
                    "건설적인 리뷰는 존중하고, 명확하며, 구체적인 개선 제안을 포함합니다. "
                    "반드시 JSON 형식으로 응답하며, 다음 키를 포함해야 합니다: "
                    "constructive_count (건설적인 리뷰 수), harsh_count (가혹한 리뷰 수), "
                    "neutral_count (중립적인 리뷰 수), suggestions (개선 제안 목록), "
                    "examples_good (좋은 예시 최대 3개), examples_improve (개선이 필요한 예시 최대 3개). "
                    "모든 응답은 한국어로 작성하세요."
                ),
            },
            {
                "role": "user",
                "content": f"다음 리뷰 코멘트들을 분석해주세요:\n\n{review_list}",
            },
        ]

        try:
            response = self.complete(messages, temperature=0.2)
            result = json.loads(response)

            return {
                "constructive_reviews": result.get("constructive_count", 0),
                "harsh_reviews": result.get("harsh_count", 0),
                "neutral_reviews": result.get("neutral_count", 0),
                "suggestions": result.get("suggestions", []),
                "examples_good": result.get("examples_good", []),
                "examples_improve": result.get("examples_improve", []),
            }
        except (ValueError, requests.RequestException, json.JSONDecodeError) as exc:
            # Fallback to simple heuristics on known errors
            logger.warning(f"LLM review tone analysis failed: {exc}")
            return self._fallback_review_tone_analysis(sample_reviews)

    def analyze_issue_quality(self, issues: List[Dict[str, str]]) -> Dict[str, Any]:
        """Analyze issue quality and clarity using LLM."""
        if not issues:
            return {
                "well_described": 0,
                "poorly_described": 0,
                "suggestions": ["이슈를 분석할 데이터가 없습니다."],
                "examples_good": [],
                "examples_poor": [],
            }

        # Sample issues (limit to 30)
        sample_issues = issues[:30]

        issue_list = "\n".join([
            f"{i+1}. #{issue['number']}: {issue['title']}\n   본문: {issue['body'][:150]}"
            for i, issue in enumerate(sample_issues)
        ])

        messages = [
            {
                "role": "system",
                "content": (
                    "당신은 프로젝트 관리 전문가입니다. GitHub 이슈의 품질을 평가하세요. "
                    "좋은 이슈는 명확한 제목, 상세한 설명, 재현 단계, 예상 결과를 포함합니다. "
                    "반드시 JSON 형식으로 응답하며, 다음 키를 포함해야 합니다: "
                    "well_described_count (잘 작성된 이슈 수), poorly_described_count (개선이 필요한 이슈 수), "
                    "suggestions (개선 제안 목록), examples_good (좋은 예시 최대 3개), "
                    "examples_poor (개선이 필요한 예시 최대 3개). 모든 응답은 한국어로 작성하세요."
                ),
            },
            {
                "role": "user",
                "content": f"다음 이슈들을 분석해주세요:\n\n{issue_list}",
            },
        ]

        try:
            response = self.complete(messages, temperature=0.2)
            result = json.loads(response)

            return {
                "well_described": result.get("well_described_count", 0),
                "poorly_described": result.get("poorly_described_count", 0),
                "suggestions": result.get("suggestions", []),
                "examples_good": result.get("examples_good", []),
                "examples_poor": result.get("examples_poor", []),
            }
        except (ValueError, requests.RequestException, json.JSONDecodeError) as exc:
            # Fallback to simple heuristics on known errors
            logger.warning(f"LLM issue analysis failed: {exc}")
            return self._fallback_issue_analysis(sample_issues)

    # Fallback analysis methods ----------------------------------------

    def _fallback_commit_analysis(self, commits: List[Dict[str, str]]) -> Dict[str, Any]:
        """Simple heuristic-based commit message analysis."""
        good_count = 0
        poor_count = 0
        examples_good = []
        examples_poor = []

        for commit in commits:
            message = commit["message"].strip()
            lines = message.split("\n")
            first_line = lines[0] if lines else ""

            # Simple heuristics
            is_good = (
                len(first_line) > 10
                and len(first_line) < 100
                and not first_line.lower().startswith(("fix", "update", "wip", "tmp"))
                and "." not in first_line[-5:]
            )

            if is_good:
                good_count += 1
                if len(examples_good) < 3:
                    examples_good.append({
                        "message": first_line,
                        "sha": commit["sha"][:7],
                    })
            else:
                poor_count += 1
                if len(examples_poor) < 3:
                    examples_poor.append({
                        "message": first_line,
                        "sha": commit["sha"][:7],
                    })

        return {
            "good_messages": good_count,
            "poor_messages": poor_count,
            "suggestions": [
                "커밋 메시지의 첫 줄은 50자 이내로 작성하세요.",
                "명령형 동사로 시작하세요 (예: Add, Fix, Update).",
                "본문에 변경 이유를 상세히 설명하세요.",
            ],
            "examples_good": examples_good,
            "examples_poor": examples_poor,
        }

    def _fallback_pr_title_analysis(self, prs: List[Dict[str, str]]) -> Dict[str, Any]:
        """Simple heuristic-based PR title analysis."""
        clear_count = 0
        vague_count = 0
        examples_good = []
        examples_poor = []

        for pr in prs:
            title = pr["title"].strip()

            # Simple heuristics
            is_clear = len(title) > 15 and len(title) < 100

            if is_clear:
                clear_count += 1
                if len(examples_good) < 3:
                    examples_good.append({
                        "number": pr["number"],
                        "title": title,
                    })
            else:
                vague_count += 1
                if len(examples_poor) < 3:
                    examples_poor.append({
                        "number": pr["number"],
                        "title": title,
                    })

        return {
            "clear_titles": clear_count,
            "vague_titles": vague_count,
            "suggestions": [
                "PR 제목은 변경 사항을 명확하게 설명하세요.",
                "너무 짧거나 모호한 제목은 피하세요.",
                "일관된 형식을 사용하세요 (예: [타입] 설명).",
            ],
            "examples_good": examples_good,
            "examples_poor": examples_poor,
        }

    def _fallback_review_tone_analysis(
        self, reviews: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """Simple heuristic-based review tone analysis."""
        constructive_count = len(reviews)
        harsh_count = 0
        neutral_count = 0

        return {
            "constructive_reviews": constructive_count,
            "harsh_reviews": harsh_count,
            "neutral_reviews": neutral_count,
            "suggestions": [
                "리뷰 코멘트는 건설적이고 존중하는 톤을 유지하세요.",
                "구체적인 개선 제안을 포함하세요.",
                "긍정적인 피드백도 함께 제공하세요.",
            ],
            "examples_good": [],
            "examples_improve": [],
        }

    def _fallback_issue_analysis(self, issues: List[Dict[str, str]]) -> Dict[str, Any]:
        """Simple heuristic-based issue quality analysis."""
        well_described = 0
        poorly_described = 0
        examples_good = []
        examples_poor = []

        for issue in issues:
            body = issue.get("body", "").strip()

            # Simple heuristics
            is_good = len(body) > 100

            if is_good:
                well_described += 1
                if len(examples_good) < 3:
                    examples_good.append({
                        "number": issue["number"],
                        "title": issue["title"],
                    })
            else:
                poorly_described += 1
                if len(examples_poor) < 3:
                    examples_poor.append({
                        "number": issue["number"],
                        "title": issue["title"],
                    })

        return {
            "well_described": well_described,
            "poorly_described": poorly_described,
            "suggestions": [
                "이슈 본문에 상세한 설명을 포함하세요.",
                "재현 단계를 명확히 작성하세요.",
                "예상 결과와 실제 결과를 비교하세요.",
            ],
            "examples_good": examples_good,
            "examples_poor": examples_poor,
        }


__all__ = ["LLMClient"]
