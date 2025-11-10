"""Utility helpers for interacting with Large Language Model endpoints."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List

import requests

from .models import PullRequestReviewBundle, ReviewPoint, ReviewSummary


@dataclass(slots=True)
class LLMClient:
    """Minimal HTTP client for chat-completion style LLM APIs."""

    endpoint: str
    model: str = ""
    timeout: int = 60

    def _build_messages(self, bundle: PullRequestReviewBundle) -> List[Dict[str, str]]:
        """Create the prompt messages describing the pull request."""

        summary_lines = [
            f"Repository: {bundle.repo}",
            f"Pull Request: #{bundle.number} {bundle.title}",
            f"Author: {bundle.author or 'unknown'}",
            f"Diff Stats: +{bundle.additions} / -{bundle.deletions} across {bundle.changed_files} files",
            "",
            "Pull Request Body:",
            bundle.body or "<empty>",
            "",
        ]

        if bundle.review_bodies:
            summary_lines.append("Existing Reviews:")
            summary_lines.extend(f"- {body}" for body in bundle.review_bodies)
            summary_lines.append("")

        if bundle.review_comments:
            summary_lines.append("Inline Review Comments:")
            summary_lines.extend(f"- {comment}" for comment in bundle.review_comments[:20])
            summary_lines.append("")

        summary_lines.append("Changed Files:")
        for file in bundle.files[:10]:
            summary_lines.append(
                f"- {file.filename} ({file.status}, +{file.additions}/-{file.deletions}, changes={file.changes})"
            )
        summary_lines.append("")

        prompt = "\n".join(summary_lines)

        return [
            {
                "role": "system",
                "content": (
                    "You are an experienced software reviewer. Provide balanced, actionable "
                    "feedback highlighting concrete strengths and improvement opportunities. "
                    "Respond strictly in JSON with keys: overview, strengths, improvements. "
                    "Each strengths/improvements entry should contain a message and an example."
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

        payloads: List[Dict[str, Any]] = [base_payload | {"response_format": {"type": "json_object"}}]
        payloads.append(base_payload)

        last_error: Exception | None = None
        for payload in payloads:
            try:
                response = requests.post(
                    self.endpoint,
                    json=payload,
                    timeout=self.timeout,
                )
                response.raise_for_status()
                return self._parse_response(response.json())
            except requests.HTTPError as exc:
                error_text = ""
                if exc.response is not None:
                    try:
                        error_text = exc.response.text
                    except Exception:  # pragma: no cover - defensive guard for rare encodings
                        error_text = ""

                if (
                    "response_format" in payload
                    and exc.response is not None
                    and exc.response.status_code in {400, 404, 422}
                    and ("json_object" in error_text or "response_format" in error_text)
                ):
                    last_error = exc
                    continue
                raise
            except Exception as exc:  # pragma: no cover - network failures already handled elsewhere
                last_error = exc
                break

        if last_error is not None:
            raise last_error

        raise RuntimeError("LLM request failed without raising an explicit error")


__all__ = ["LLMClient"]
