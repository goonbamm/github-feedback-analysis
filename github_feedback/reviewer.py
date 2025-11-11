"""Pull request review orchestration for GitHub feedback analysis."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List

from .collector import Collector
from .console import Console
from .llm import LLMClient
from .models import PullRequestReviewBundle, ReviewPoint, ReviewSummary
from .utils import truncate_patch

console = Console()


@dataclass(slots=True)
class Reviewer:
    """Coordinate pull request data collection and LLM review generation."""

    collector: Collector
    llm: LLMClient | None = None
    output_dir: Path = Path("reviews")

    def _target_dir(self, repo: str, number: int) -> Path:
        safe_repo = repo.replace("/", "__")
        return self.output_dir / safe_repo / f"pr-{number}"

    def persist_bundle(self, bundle: PullRequestReviewBundle) -> Path:
        """Persist collected artefacts to disk for later reuse."""

        target_dir = self._target_dir(bundle.repo, bundle.number)
        target_dir.mkdir(parents=True, exist_ok=True)
        artefact_path = target_dir / "artefacts.json"
        artefact_path.write_text(
            json.dumps(bundle.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return artefact_path

    def persist_summary(
        self, bundle: PullRequestReviewBundle, summary: ReviewSummary
    ) -> Path:
        """Store the structured LLM response for traceability."""

        target_dir = self._target_dir(bundle.repo, bundle.number)
        target_dir.mkdir(parents=True, exist_ok=True)
        summary_path = target_dir / "review_summary.json"
        summary_path.write_text(
            json.dumps(summary.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return summary_path

    def _fallback_summary(self, bundle: PullRequestReviewBundle) -> ReviewSummary:
        """Provide a deterministic summary when the LLM cannot be reached."""

        overview = (
            f"Pull Request #{bundle.number}는 {bundle.changed_files}개 파일을 수정했으며, "
            f"+{bundle.additions} 추가, -{bundle.deletions} 삭제가 있습니다."
        )

        strengths: List[ReviewPoint] = []
        if bundle.body.strip():
            strengths.append(
                ReviewPoint(
                    message="Pull Request 설명이 의도를 명확히 설명하고 있습니다.",
                    example=bundle.body.strip().splitlines()[0],
                )
            )
        if bundle.files:
            first_file = bundle.files[0]
            strengths.append(
                ReviewPoint(
                    message=f"`{first_file.filename}`에 집중된 변경사항이 포함되어 있습니다.",
                    example=truncate_patch(first_file.patch or ""),
                )
            )

        improvements: List[ReviewPoint] = []
        if not bundle.review_comments:
            improvements.append(
                ReviewPoint(
                    message="리뷰어를 돕기 위해 셀프 리뷰 코멘트를 추가하는 것을 고려해보세요.",
                    example="Pull Request에 인라인 코멘트가 제공되지 않았습니다.",
                )
            )
        if bundle.files:
            improvements.append(
                ReviewPoint(
                    message="회귀 테스트에 영향이 있는지 다시 확인해보세요.",
                    example=f"`{bundle.files[-1].filename}`의 변경사항에 대한 테스트 커버리지 갭을 검토하세요.",
                )
            )

        return ReviewSummary(overview=overview, strengths=strengths, improvements=improvements)

    def generate_summary(self, bundle: PullRequestReviewBundle) -> ReviewSummary:
        """Request LLM feedback while falling back gracefully when required."""

        if not self.llm:
            console.log("LLM client not configured; using fallback summary")
            return self._fallback_summary(bundle)

        try:
            summary = self.llm.generate_review(bundle)
        except Exception as exc:  # pragma: no cover - network errors are hard to simulate
            console.log("LLM generation failed", str(exc))
            summary = self._fallback_summary(bundle)

        if not summary.overview:
            summary.overview = (
                f"Pull Request #{bundle.number}는 {bundle.changed_files}개 파일에 걸쳐 "
                f"{bundle.additions}개 추가 및 {bundle.deletions}개 삭제가 있습니다."
            )

        return summary

    def create_markdown(
        self, bundle: PullRequestReviewBundle, summary: ReviewSummary
    ) -> Path:
        """Create a high readability markdown review with generous spacing."""

        target_dir = self._target_dir(bundle.repo, bundle.number)
        target_dir.mkdir(parents=True, exist_ok=True)
        markdown_path = target_dir / "review.md"

        lines: List[str] = []
        lines.append("# Pull Request 리뷰")
        lines.append("")
        lines.append(f"저장소 : **{bundle.repo}**")
        lines.append(f"Pull Request : **#{bundle.number} {bundle.title}**")
        lines.append("")
        lines.append(f"작성자 : **{bundle.author or 'unknown'}**")
        lines.append(f"URL : {bundle.html_url}")
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("## 개요")
        lines.append("")
        lines.append(summary.overview)
        lines.append("")

        def _render_points(title: str, points: Iterable[ReviewPoint]) -> None:
            lines.append(f"## {title}")
            lines.append("")
            has_points = False
            for point in points:
                has_points = True
                lines.append(f"- {point.message}")
                if point.example:
                    lines.append("")
                    lines.append(f"  _예시:_ {point.example}")
                    lines.append("")
                else:
                    lines.append("")
            if not has_points:
                lines.append("- 기록된 항목이 없습니다.")
                lines.append("")

        _render_points("장점", summary.strengths)
        _render_points("개선할 부분", summary.improvements)

        lines.append("## 코드 하이라이트")
        lines.append("")
        if not bundle.files:
            lines.append("- 파일 변경사항이 감지되지 않았습니다.")
        else:
            for file in bundle.files[:5]:
                lines.append(
                    f"- `{file.filename}` — {file.changes}개 변경 ( +{file.additions} / -{file.deletions} )"
                )
                if file.patch:
                    lines.append("")
                    lines.append("```diff")
                    lines.append(truncate_patch(file.patch))
                    lines.append("```")
                    lines.append("")
                else:
                    lines.append("")

        lines.append("")
        lines.append("## 저장된 파일")
        lines.append("")
        lines.append("- `artefacts.json` 파일에 원본 Pull Request 데이터가 포함되어 있습니다.")
        lines.append("- `review_summary.json` 파일에 구조화된 LLM 응답이 저장되어 있습니다.")
        lines.append("")

        markdown_path.write_text("\n".join(lines), encoding="utf-8")
        return markdown_path

    def review_pull_request(self, repo: str, number: int) -> tuple[str, Path, Path, Path]:
        """End-to-end review helper used by the CLI command.

        Returns:
            Tuple of (pr_title, artefact_path, summary_path, markdown_path)
        """

        bundle = self.collector.collect_pull_request_details(repo=repo, number=number)
        artefact_path = self.persist_bundle(bundle)
        summary = self.generate_summary(bundle)
        summary_path = self.persist_summary(bundle, summary)
        markdown_path = self.create_markdown(bundle, summary)
        return bundle.title, artefact_path, summary_path, markdown_path


__all__ = ["Reviewer"]
