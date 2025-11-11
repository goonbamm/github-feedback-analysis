"""Aggregate pull request reviews into an integrated annual report."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List

from .console import Console
from .llm import LLMClient
from .models import ReviewPoint

console = Console()


@dataclass(slots=True)
class StoredReview:
    """Stored review summary reconstructed from cached artefacts."""

    number: int
    title: str
    author: str
    html_url: str
    created_at: datetime
    overview: str
    strengths: List[ReviewPoint]
    improvements: List[ReviewPoint]


class ReviewReporter:
    """Build integrated Korean reports from individual pull request reviews."""

    def __init__(self, *, output_dir: Path = Path("reviews"), llm: LLMClient | None = None) -> None:
        self.output_dir = output_dir
        self.llm = llm

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _repo_dir(self, repo: str) -> Path:
        safe_repo = repo.replace("/", "__")
        return self.output_dir / safe_repo

    @staticmethod
    def _load_points(raw_points: Iterable[dict]) -> List[ReviewPoint]:
        points: List[ReviewPoint] = []
        for payload in raw_points:
            if not isinstance(payload, dict):
                continue
            message = str(payload.get("message") or "").strip()
            if not message:
                continue
            example_raw = payload.get("example")
            example = str(example_raw).strip() if example_raw else None
            points.append(ReviewPoint(message=message, example=example))
        return points

    def _load_reviews(self, repo: str) -> List[StoredReview]:
        repo_dir = self._repo_dir(repo)
        if not repo_dir.exists():
            return []

        reviews: List[StoredReview] = []
        for pr_dir in sorted(repo_dir.glob("pr-*")):
            summary_path = pr_dir / "review_summary.json"
            artefact_path = pr_dir / "artefacts.json"
            if not summary_path.exists() or not artefact_path.exists():
                continue

            try:
                summary_data = json.loads(summary_path.read_text(encoding="utf-8"))
                artefact_data = json.loads(artefact_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                console.log("Skipping invalid review artefact", str(pr_dir))
                continue

            try:
                number = int(artefact_data.get("number"))
                title = str(artefact_data.get("title") or "").strip()
                author = str(artefact_data.get("author") or "unknown").strip()
                html_url = str(artefact_data.get("html_url") or "").strip()
                created_at_raw = artefact_data.get("created_at")
                created_at = (
                    datetime.fromisoformat(created_at_raw)
                    if isinstance(created_at_raw, str)
                    else datetime.now(timezone.utc)
                )
            except Exception:  # pragma: no cover - defensive parsing guard
                console.log("Skipping malformed artefact", str(pr_dir))
                continue

            overview = str(summary_data.get("overview") or "").strip()
            strengths = self._load_points(summary_data.get("strengths", []))
            improvements = self._load_points(summary_data.get("improvements", []))

            reviews.append(
                StoredReview(
                    number=number,
                    title=title,
                    author=author,
                    html_url=html_url,
                    created_at=created_at,
                    overview=overview,
                    strengths=strengths,
                    improvements=improvements,
                )
            )

        reviews.sort(key=lambda item: (item.created_at, item.number))
        return reviews

    def _build_prompt_context(self, repo: str, reviews: List[StoredReview]) -> str:
        lines: List[str] = []
        lines.append(f"Repository: {repo}")
        lines.append(f"총 리뷰 PR 수: {len(reviews)}")
        lines.append("")
        lines.append("Pull Request 요약:")
        for review in reviews:
            lines.append(
                f"- PR #{review.number} {review.title} (작성자: {review.author}, 생성일: {review.created_at.date()})"
            )
            if review.html_url:
                lines.append(f"  URL: {review.html_url}")
            if review.overview:
                lines.append(f"  Overview: {review.overview}")
            if review.strengths:
                lines.append("  Strengths:")
                for point in review.strengths:
                    lines.append(f"    • {point.message}")
                    if point.example:
                        lines.append(f"      예시: {point.example}")
            if review.improvements:
                lines.append("  Improvements:")
                for point in review.improvements:
                    lines.append(f"    • {point.message}")
                    if point.example:
                        lines.append(f"      예시: {point.example}")
            lines.append("")

        return "\n".join(lines).strip()

    # ------------------------------------------------------------------
    # Reporting
    # ------------------------------------------------------------------

    def _fallback_report(self, repo: str, reviews: List[StoredReview]) -> str:
        lines: List[str] = []
        lines.append("# 통합 코드 리뷰 보고서")
        lines.append("")
        lines.append(f"- 저장소: **{repo}**")
        lines.append(f"- 검토한 PR 수: **{len(reviews)}건**")
        lines.append("")

        def _render_points(title: str, entries: List[tuple[StoredReview, ReviewPoint]]) -> None:
            lines.append(f"## {title}")
            lines.append("")
            if not entries:
                lines.append("- 수집된 항목이 없습니다.")
                lines.append("")
                return

            for review, point in entries:
                bullet = f"- PR #{review.number} {review.title}: {point.message}"
                lines.append(bullet)
                if point.example:
                    lines.append(f"  - 예시: {point.example}")
                lines.append("")

        strength_entries: List[tuple[StoredReview, ReviewPoint]] = []
        improvement_entries: List[tuple[StoredReview, ReviewPoint]] = []

        for review in reviews:
            strength_entries.extend((review, point) for point in review.strengths)
            improvement_entries.extend((review, point) for point in review.improvements)

        _render_points("장점", strength_entries[:8])
        _render_points("보완점", improvement_entries[:8])

        lines.append("## 올해 성장한 점")
        lines.append("")
        growth_items = [review for review in reviews if review.overview]
        if not growth_items:
            lines.append("- 개별 리뷰 요약이 없어 성장 포인트를 추론하기 어렵습니다.")
        else:
            for review in growth_items[:8]:
                lines.append(
                    f"- PR #{review.number} {review.title} 회고: {review.overview}"
                )
        lines.append("")

        lines.append("## 전체 총평")
        lines.append("")
        lines.append(
            "- 저장된 리뷰 요약을 바탕으로 팀이 지속해서 지식을 공유하고 있으며, "
            "통합 보고서를 통해 반복되는 강점과 개선점을 추적할 수 있습니다."
        )
        lines.append("")

        lines.append("## 개별 PR 하이라이트")
        lines.append("")
        for review in reviews:
            highlight = f"- PR #{review.number} {review.title}"
            if review.html_url:
                highlight += f" ({review.html_url})"
            lines.append(highlight)
        lines.append("")

        return "\n".join(lines).strip()

    def _generate_report_text(self, repo: str, reviews: List[StoredReview]) -> str:
        if not self.llm:
            return self._fallback_report(repo, reviews)

        context = self._build_prompt_context(repo, reviews)
        instructions = (
            "당신은 소프트웨어 팀의 리드입니다. 아래 Pull Request 리뷰 요약을 토대로 한국어로 "
            "통합 피드백 보고서를 작성하세요. 보고서는 Markdown 형식이어야 하며 반드시 다음 섹션을 포함해야 합니다: "
            "## 장점, ## 보완점, ## 올해 성장한 점, ## 전체 총평. 각 섹션에는 구체적인 근거, 영향, 다음 액션을 명시해 주세요."
        )

        messages = [
            {
                "role": "system",
                "content": (
                    "당신은 팀과 개인의 성장을 촉진하는 기술 리더입니다."
                    " 상세한 데이터를 바탕으로 실질적인 피드백을 제시하세요."
                ),
            },
            {
                "role": "user",
                "content": f"{instructions}\n\n{context}",
            },
        ]

        try:
            content = self.llm.complete(messages, temperature=0.25)
            if content.strip():
                return content.strip()
        except Exception as exc:  # pragma: no cover - network errors hard to simulate
            console.log("LLM 통합 보고서 생성 실패", str(exc))

        return self._fallback_report(repo, reviews)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def create_integrated_report(self, repo: str) -> Path:
        """Create or refresh the integrated review report for a repository."""

        repo_input = repo.strip()
        if not repo_input:
            raise ValueError("Repository cannot be empty")

        reviews = self._load_reviews(repo_input)
        if not reviews:
            raise ValueError("No review summaries found for the given repository")

        report_text = self._generate_report_text(repo_input, reviews)

        repo_dir = self._repo_dir(repo_input)
        repo_dir.mkdir(parents=True, exist_ok=True)
        report_path = repo_dir / "integrated_report.md"
        report_path.write_text(report_text, encoding="utf-8")
        return report_path


__all__ = ["ReviewReporter", "StoredReview"]
