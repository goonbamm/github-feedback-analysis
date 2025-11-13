"""Utility helpers for interacting with Large Language Model endpoints."""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List

import requests

from .constants import LLM_DEFAULTS, THREAD_POOL_CONFIG
from .models import PullRequestReviewBundle, ReviewPoint, ReviewSummary
from .utils import limit_items, truncate_patch

logger = logging.getLogger(__name__)


# Default values (used when config is not available)
MAX_PATCH_LINES_PER_FILE = LLM_DEFAULTS['max_patch_lines_per_file']
MAX_FILES_WITH_PATCH_SNIPPETS = LLM_DEFAULTS['max_files_with_patch_snippets']


@dataclass(slots=True)
class LLMClient:
    """Minimal HTTP client for chat-completion style LLM APIs."""

    endpoint: str
    model: str = ""
    timeout: int = 60
    max_files_in_prompt: int = 10
    max_files_with_patch_snippets: int = 5

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
        for index, file in enumerate(limit_items(bundle.files, self.max_files_in_prompt)):
            summary_lines.append(
                f"- {file.filename} ({file.status}, +{file.additions}/-{file.deletions}, 변경={file.changes})"
            )
            if (
                index < self.max_files_with_patch_snippets
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
                    "당신은 시니어 소프트웨어 엔지니어로서 코드 리뷰를 수행합니다.\n\n"
                    "다음 원칙을 따르세요:\n"
                    "1. 보안, 성능, 가독성, 유지보수성 순으로 우선순위 평가\n"
                    "2. 각 피드백에 구체적 근거와 개선 방법 제시\n"
                    "3. 긍정적 피드백과 개선점을 균형있게 제공 (최소 1:1 비율)\n"
                    "4. 코드 컨텍스트가 제한적이면 \"전체 컨텍스트 확인 필요\" 명시\n\n"
                    "응답은 반드시 다음 JSON 형식을 따르세요:\n\n"
                    "{\n"
                    '  "overview": "PR의 전반적 평가 (2-3문장)",\n'
                    '  "strengths": [\n'
                    "    {\n"
                    '      "message": "장점 설명",\n'
                    '      "example": "관련 코드나 파일명",\n'
                    '      "impact": "high|medium|low"\n'
                    "    }\n"
                    "  ],\n"
                    '  "improvements": [\n'
                    "    {\n"
                    '      "message": "개선 제안",\n'
                    '      "example": "구체적 코드 예시나 위치",\n'
                    '      "priority": "critical|important|nice-to-have",\n'
                    '      "category": "security|performance|readability|maintainability|testing"\n'
                    "    }\n"
                    "  ]\n"
                    "}\n\n"
                    "각 배열은 최소 1개, 최대 5개 항목을 포함하세요. 모든 응답은 한국어로 작성하세요."
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
            "temperature": 0.3,
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

    def test_connection(self) -> None:
        """Test connection to the LLM endpoint with a simple request.

        Raises:
            requests.RequestException: If connection fails
            ValueError: If response format is invalid
        """
        test_messages = [
            {
                "role": "system",
                "content": "You are a helpful assistant.",
            },
            {
                "role": "user",
                "content": "Hello",
            },
        ]

        payload = {
            "model": self.model or "default-model",
            "messages": test_messages,
            "temperature": 0.1,
            "max_tokens": 10,
        }

        # Use shorter timeout for test connection
        test_timeout = THREAD_POOL_CONFIG['test_connection_timeout']
        response = requests.post(
            self.endpoint,
            json=payload,
            timeout=min(self.timeout, test_timeout),
        )
        response.raise_for_status()

        try:
            response_payload = response.json()
        except ValueError as exc:
            raise ValueError("LLM endpoint returned invalid JSON") from exc

        choices = response_payload.get("choices")
        if not choices:
            raise ValueError("LLM endpoint response format is invalid (missing 'choices')")

    def complete(
        self,
        messages: List[Dict[str, str]],
        *,
        temperature: float = 0.3,
        max_retries: int = 3,
        retry_delay: float = 2.0,
    ) -> str:
        """Execute a generic chat completion request with retry logic.

        Args:
            messages: Chat messages for the LLM
            temperature: Sampling temperature
            max_retries: Maximum number of retry attempts (default: 3)
            retry_delay: Base delay between retries in seconds (default: 2.0)

        Returns:
            LLM response content

        Raises:
            ValueError: If response is invalid after all retries
            requests.HTTPError: If HTTP error persists after all retries
        """

        payload = {
            "model": self.model or "default-model",
            "messages": messages,
            "temperature": temperature,
        }

        last_exception = None

        for attempt in range(max_retries + 1):
            try:
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

                # Success! Log if this was a retry
                if attempt > 0:
                    logger.info(f"LLM request succeeded on attempt {attempt + 1}")

                return content

            except (requests.RequestException, ValueError) as exc:
                last_exception = exc

                # Don't retry on certain errors
                if isinstance(exc, requests.HTTPError):
                    status_code = exc.response.status_code
                    # Don't retry on client errors (except rate limit and timeout)
                    if 400 <= status_code < 500 and status_code not in [429, 408]:
                        logger.error(f"LLM request failed with status {status_code}: {exc}")
                        raise

                # Log the error and retry if we have attempts left
                if attempt < max_retries:
                    # Exponential backoff: 2s, 4s, 8s
                    delay = retry_delay * (2 ** attempt)
                    logger.warning(
                        f"LLM request failed (attempt {attempt + 1}/{max_retries + 1}): {exc}. "
                        f"Retrying in {delay}s..."
                    )
                    time.sleep(delay)
                else:
                    logger.error(
                        f"LLM request failed after {max_retries + 1} attempts: {exc}"
                    )

        # If we get here, all retries failed
        raise last_exception  # type: ignore

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

        # Sample commits for analysis (limit to 20)
        sample_commits = commits[:20]

        commit_list = "\n".join([
            f"{i+1}. {commit['message'][:100]} (SHA: {commit['sha'][:7]})"
            for i, commit in enumerate(sample_commits)
        ])

        messages = [
            {
                "role": "system",
                "content": (
                    "당신은 Git 커밋 메시지 품질을 평가하는 전문가입니다.\n\n"
                    "다음 기준으로 평가하세요:\n\n"
                    "**좋은 커밋 메시지 기준:**\n"
                    "1. 첫 줄: 50자 이내, 명령형 동사 시작 (Add, Fix, Update, Refactor 등)\n"
                    "2. 본문: 왜(why) 변경했는지 설명 (무엇을 변경했는지는 코드로 알 수 있음)\n"
                    "3. Conventional Commits 형식 권장: `type(scope): subject`\n"
                    "4. Issue/PR 번호 참조 포함\n"
                    "5. 여러 변경사항은 여러 커밋으로 분리\n\n"
                    "**나쁜 커밋 메시지 예:**\n"
                    '- "fix", "update", "wip", "tmp" 같은 단어만 사용\n'
                    "- 변경 내용 나열만 하고 이유 없음\n"
                    "- 너무 길거나 (100자+) 짧음 (10자-)\n\n"
                    "응답 형식:\n"
                    "{\n"
                    '  "good_count": 숫자,\n'
                    '  "poor_count": 숫자,\n'
                    '  "suggestions": [\n'
                    '    "구체적이고 실행 가능한 개선 제안"\n'
                    "  ],\n"
                    '  "examples_good": [\n'
                    "    {\n"
                    '      "sha": "커밋 해시",\n'
                    '      "message": "커밋 메시지",\n'
                    '      "reason": "왜 좋은지 설명"\n'
                    "    }\n"
                    "  ],\n"
                    '  "examples_poor": [\n'
                    "    {\n"
                    '      "sha": "커밋 해시",\n'
                    '      "message": "커밋 메시지",\n'
                    '      "reason": "왜 개선이 필요한지",\n'
                    '      "suggestion": "개선 방법"\n'
                    "    }\n"
                    "  ],\n"
                    '  "trends": {\n'
                    '    "common_patterns": ["발견된 패턴"],\n'
                    '    "improvement_areas": ["개선 영역"]\n'
                    "  }\n"
                    "}\n\n"
                    "최대 20개 샘플만 분석하고, 대표적인 예시를 선정하세요. 모든 응답은 한국어로 작성하세요."
                ),
            },
            {
                "role": "user",
                "content": f"다음 커밋 메시지들을 분석해주세요:\n\n{commit_list}",
            },
        ]

        try:
            response = self.complete(messages, temperature=0.3)
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

        # Sample PR titles for analysis (limit to 20)
        sample_prs = pr_titles[:20]

        pr_list = "\n".join([
            f"{i+1}. #{pr['number']}: {pr['title']}"
            for i, pr in enumerate(sample_prs)
        ])

        messages = [
            {
                "role": "system",
                "content": (
                    "당신은 Pull Request 제목 품질을 평가하는 전문가입니다.\n\n"
                    "**좋은 PR 제목 기준:**\n"
                    "1. 길이: 15-80자 (너무 짧거나 길지 않게)\n"
                    "2. 형식: `[타입] 명확한 변경 내용 설명`\n"
                    "   - 타입 예: Feature, Fix, Refactor, Docs, Test, Chore\n"
                    "3. 변경의 범위와 영향 명시\n"
                    "4. 단순 파일명 나열 금지\n"
                    "5. Issue 번호 참조 권장\n\n"
                    "**명확성 체크리스트:**\n"
                    "- [ ] 제목만 읽고도 변경 내용 이해 가능한가?\n"
                    "- [ ] 구체적인 동사 사용했는가?\n"
                    "- [ ] 사용자 관점의 가치가 드러나는가?\n\n"
                    "**나쁜 예:**\n"
                    '- "Update code" (무엇을 왜?)\n'
                    '- "fix" (무엇을 수정?)\n'
                    '- "Implement feature/login/api/..." (구체성 부족)\n\n'
                    "응답 형식:\n"
                    "{\n"
                    '  "clear_count": 숫자,\n'
                    '  "vague_count": 숫자,\n'
                    '  "suggestions": [\n'
                    '    "팀 전체에 적용 가능한 구체적 가이드라인"\n'
                    "  ],\n"
                    '  "examples_good": [\n'
                    "    {\n"
                    '      "number": PR 번호,\n'
                    '      "title": "제목",\n'
                    '      "reason": "왜 명확한지",\n'
                    '      "score": 1-10\n'
                    "    }\n"
                    "  ],\n"
                    '  "examples_poor": [\n'
                    "    {\n"
                    '      "number": PR 번호,\n'
                    '      "title": "제목",\n'
                    '      "reason": "왜 모호한지",\n'
                    '      "suggestion": "개선된 제목 예시"\n'
                    "    }\n"
                    "  ],\n"
                    '  "patterns": {\n'
                    '    "common_types": ["발견된 타입들"],\n'
                    '    "naming_conventions": ["사용중인 컨벤션"]\n'
                    "  }\n"
                    "}\n\n"
                    "모든 응답은 한국어로 작성하세요."
                ),
            },
            {
                "role": "user",
                "content": f"다음 PR 제목들을 분석해주세요:\n\n{pr_list}",
            },
        ]

        try:
            response = self.complete(messages, temperature=0.3)
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

        # Sample review comments (limit to 15)
        sample_reviews = review_comments[:15]

        review_list = "\n".join([
            f"{i+1}. (PR #{review['pr_number']}, {review['author']}): {review['body'][:200]}"
            for i, review in enumerate(sample_reviews)
        ])

        messages = [
            {
                "role": "system",
                "content": (
                    "당신은 팀 협업과 커뮤니케이션 전문가입니다.\n"
                    "코드 리뷰 코멘트의 톤을 분석하고 개선 방안을 제시하세요.\n\n"
                    "**평가 기준:**\n\n"
                    "건설적인 리뷰 (Constructive):\n"
                    "- 구체적 문제 지적 + 해결 방법 제안\n"
                    '- 존중하는 표현 사용 ("~하면 어떨까요?", "~를 고려해보세요")\n'
                    "- 코드에 집중, 사람 비판 X\n"
                    "- 긍정적 피드백 포함\n"
                    '- 예: "이 부분을 함수로 분리하면 테스트하기 쉬울 것 같아요."\n\n'
                    "가혹한 리뷰 (Harsh):\n"
                    '- 명령형/단정적 표현 ("이건 잘못됐어요", "다시 해야 합니다")\n'
                    "- 근거 없는 비판\n"
                    "- 작성자 능력 폄하\n"
                    '- 예: "이건 완전히 잘못된 접근입니다."\n\n'
                    "중립적 리뷰 (Neutral):\n"
                    "- 단순 사실 지적, 개선 방안 없음\n"
                    "- 감정적 톤 없음\n"
                    '- 예: "이 함수는 너무 깁니다."\n\n'
                    "**한국 개발 문화 고려사항:**\n"
                    "- 직접적 표현도 맥락에 따라 건설적일 수 있음\n"
                    "- 높임말 사용 여부보다 내용의 구체성이 중요\n"
                    "- 이모지 사용은 긍정적 신호일 수 있음\n\n"
                    "응답 형식:\n"
                    "{\n"
                    '  "constructive_count": 숫자,\n'
                    '  "harsh_count": 숫자,\n'
                    '  "neutral_count": 숫자,\n'
                    '  "suggestions": [\n'
                    '    "팀 전체 커뮤니케이션 개선 제안"\n'
                    "  ],\n"
                    '  "examples_good": [\n'
                    "    {\n"
                    '      "pr_number": PR 번호,\n'
                    '      "author": "작성자",\n'
                    '      "comment": "코멘트 내용",\n'
                    '      "strengths": ["좋은 점들"]\n'
                    "    }\n"
                    "  ],\n"
                    '  "examples_improve": [\n'
                    "    {\n"
                    '      "pr_number": PR 번호,\n'
                    '      "author": "작성자",\n'
                    '      "comment": "원본 코멘트",\n'
                    '      "issues": ["문제점들"],\n'
                    '      "improved_version": "개선된 표현 예시"\n'
                    "    }\n"
                    "  ],\n"
                    '  "team_culture_insights": {\n'
                    '    "positive_patterns": ["발견된 긍정적 패턴"],\n'
                    '    "areas_for_growth": ["개선 영역"]\n'
                    "  }\n"
                    "}\n\n"
                    "각 카테고리에 명확히 분류하고, 경계선상의 경우 맥락을 고려하세요. 모든 응답은 한국어로 작성하세요."
                ),
            },
            {
                "role": "user",
                "content": f"다음 리뷰 코멘트들을 분석해주세요:\n\n{review_list}",
            },
        ]

        try:
            response = self.complete(messages, temperature=0.3)
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

        # Sample issues (limit to 15)
        sample_issues = issues[:15]

        issue_list = "\n".join([
            f"{i+1}. #{issue['number']}: {issue['title']}\n   본문: {issue['body'][:150]}"
            for i, issue in enumerate(sample_issues)
        ])

        messages = [
            {
                "role": "system",
                "content": (
                    "당신은 프로젝트 관리 전문가로서 GitHub 이슈 품질을 평가합니다.\n\n"
                    "**이슈 타입별 기준:**\n\n"
                    "Bug Report:\n"
                    "- [ ] 명확한 재현 단계\n"
                    "- [ ] 예상 결과 vs 실제 결과\n"
                    "- [ ] 환경 정보 (OS, 버전 등)\n"
                    "- [ ] 에러 메시지나 스크린샷\n"
                    "- [ ] 영향 범위\n\n"
                    "Feature Request:\n"
                    "- [ ] 해결하려는 문제 설명\n"
                    "- [ ] 제안하는 솔루션\n"
                    "- [ ] 대안 고려사항\n"
                    "- [ ] 사용자 시나리오\n"
                    "- [ ] 우선순위 근거\n\n"
                    "일반 이슈:\n"
                    "- [ ] 명확한 제목 (타입 포함)\n"
                    "- [ ] 상세한 설명 (단순 요청 이상)\n"
                    "- [ ] 라벨이나 마일스톤 설정 가능성\n"
                    "- [ ] 관련 이슈/PR 링크\n\n"
                    "**품질 평가:**\n"
                    "- 잘 작성됨: 위 체크리스트 70% 이상 충족\n"
                    "- 개선 필요: 체크리스트 50% 미만 또는 핵심 정보 누락\n\n"
                    "응답 형식:\n"
                    "{\n"
                    '  "well_described_count": 숫자,\n'
                    '  "poorly_described_count": 숫자,\n'
                    '  "type_breakdown": {\n'
                    '    "bug": 숫자,\n'
                    '    "feature": 숫자,\n'
                    '    "question": 숫자,\n'
                    '    "other": 숫자\n'
                    "  },\n"
                    '  "suggestions": [\n'
                    '    "이슈 템플릿 개선 제안",\n'
                    '    "작성 가이드라인"\n'
                    "  ],\n"
                    '  "examples_good": [\n'
                    "    {\n"
                    '      "number": 이슈 번호,\n'
                    '      "title": "제목",\n'
                    '      "type": "bug|feature|other",\n'
                    '      "strengths": ["잘된 점들"],\n'
                    '      "completeness_score": 1-10\n'
                    "    }\n"
                    "  ],\n"
                    '  "examples_poor": [\n'
                    "    {\n"
                    '      "number": 이슈 번호,\n'
                    '      "title": "제목",\n'
                    '      "missing_elements": ["누락된 요소들"],\n'
                    '      "suggestion": "개선 방법"\n'
                    "    }\n"
                    "  ],\n"
                    '  "template_recommendations": [\n'
                    '    "프로젝트에 권장하는 이슈 템플릿 형식"\n'
                    "  ]\n"
                    "}\n\n"
                    "모든 응답은 한국어로 작성하세요."
                ),
            },
            {
                "role": "user",
                "content": f"다음 이슈들을 분석해주세요:\n\n{issue_list}",
            },
        ]

        try:
            response = self.complete(messages, temperature=0.3)
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
