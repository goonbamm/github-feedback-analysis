"""Utility helpers for interacting with Large Language Model endpoints."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List

import requests

from .models import PullRequestReviewBundle, ReviewPoint, ReviewSummary
from .utils import limit_items, truncate_patch


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


__all__ = ["LLMClient"]
