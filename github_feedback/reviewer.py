"""Pull request review orchestration for GitHub feedback analysis."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List

import requests

from .collector import Collector
from .console import Console
from .llm import LLMClient
from .models import PullRequestReviewBundle, ReviewPoint, ReviewSummary
from .utils import truncate_patch

console = Console()
logger = logging.getLogger(__name__)

# Review file constants
ARTEFACTS_FILENAME = "artefacts.json"
REVIEW_SUMMARY_FILENAME = "review_summary.json"
REVIEW_MARKDOWN_FILENAME = "review.md"


@dataclass(slots=True)
class Reviewer:
    """Coordinate pull request data collection and LLM review generation."""

    collector: Collector
    llm: LLMClient | None = None
    output_dir: Path = Path("reports/reviews")

    def _target_dir(self, repo: str, number: int) -> Path:
        safe_repo = repo.replace("/", "__")
        return self.output_dir / safe_repo / f"pr-{number}"

    def _ensure_target_dir(self, repo: str, number: int) -> Path:
        """Create and return the target directory for PR review files."""

        target_dir = self._target_dir(repo, number)
        try:
            target_dir.mkdir(parents=True, exist_ok=True)
        except (OSError, PermissionError) as exc:
            logger.error(f"Failed to create directory {target_dir}: {exc}")
            raise
        return target_dir

    def _write_json(self, path: Path, data: dict) -> None:
        """Write JSON data to a file with consistent formatting."""

        try:
            path.write_text(
                json.dumps(data, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        except (OSError, PermissionError) as exc:
            logger.error(f"Failed to write JSON to {path}: {exc}")
            raise

    def persist_bundle(self, bundle: PullRequestReviewBundle) -> Path:
        """Persist collected artefacts to disk for later reuse."""

        target_dir = self._ensure_target_dir(bundle.repo, bundle.number)
        artefact_path = target_dir / ARTEFACTS_FILENAME
        self._write_json(artefact_path, bundle.to_dict())
        return artefact_path

    def persist_summary(
        self, bundle: PullRequestReviewBundle, summary: ReviewSummary
    ) -> Path:
        """Store the structured LLM response for traceability."""

        target_dir = self._ensure_target_dir(bundle.repo, bundle.number)
        summary_path = target_dir / REVIEW_SUMMARY_FILENAME
        self._write_json(summary_path, summary.to_dict())
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
        except requests.HTTPError as exc:  # pragma: no cover - network errors are hard to simulate
            logger.error(f"LLM HTTP error for PR #{bundle.number}: {exc.response.status_code if exc.response else 'unknown'}")
            console.log(f"LLM generation failed (HTTP error), using fallback summary")
            summary = self._fallback_summary(bundle)
        except Exception as exc:
            logger.error(f"LLM generation error for PR #{bundle.number}: {exc}")
            console.log(f"LLM generation failed ({type(exc).__name__}), using fallback summary")
            summary = self._fallback_summary(bundle)

        if not summary.overview:
            summary.overview = (
                f"Pull Request #{bundle.number}는 {bundle.changed_files}개 파일에 걸쳐 "
                f"{bundle.additions}개 추가 및 {bundle.deletions}개 삭제가 있습니다."
            )

        return summary

    def _render_markdown_header(self, bundle: PullRequestReviewBundle) -> List[str]:
        """Render the markdown header section with PR metadata."""

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
        return lines

    def _render_markdown_overview(self, summary: ReviewSummary) -> List[str]:
        """Render the overview section of the markdown."""

        lines: List[str] = []
        lines.append("## 개요")
        lines.append("")
        lines.append(summary.overview)
        lines.append("")
        return lines

    def _render_markdown_points(self, title: str, points: Iterable[ReviewPoint]) -> List[str]:
        """Render a section of review points (strengths or improvements)."""

        lines: List[str] = []
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
        return lines

    def _render_markdown_code_highlights(self, bundle: PullRequestReviewBundle) -> List[str]:
        """Render the code highlights section with file changes."""

        lines: List[str] = []
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
        return lines

    def _render_markdown_footer(self) -> List[str]:
        """Render the footer section with saved files information."""

        lines: List[str] = []
        lines.append("## 저장된 파일")
        lines.append("")
        lines.append(f"- `{ARTEFACTS_FILENAME}` 파일에 원본 Pull Request 데이터가 포함되어 있습니다.")
        lines.append(f"- `{REVIEW_SUMMARY_FILENAME}` 파일에 구조화된 LLM 응답이 저장되어 있습니다.")
        lines.append("")
        return lines

    def create_markdown(
        self, bundle: PullRequestReviewBundle, summary: ReviewSummary
    ) -> Path:
        """Create a high readability markdown review with generous spacing."""

        target_dir = self._ensure_target_dir(bundle.repo, bundle.number)
        markdown_path = target_dir / REVIEW_MARKDOWN_FILENAME

        lines: List[str] = []
        lines.extend(self._render_markdown_header(bundle))
        lines.extend(self._render_markdown_overview(summary))
        lines.extend(self._render_markdown_points("장점", summary.strengths))
        lines.extend(self._render_markdown_points("개선할 부분", summary.improvements))
        lines.extend(self._render_markdown_code_highlights(bundle))
        lines.extend(self._render_markdown_footer())

        try:
            markdown_path.write_text("\n".join(lines), encoding="utf-8")
        except (OSError, PermissionError) as exc:
            logger.error(f"Failed to write markdown to {markdown_path}: {exc}")
            raise
        return markdown_path

    def review_pull_request(self, repo: str, number: int) -> tuple[Path, Path, Path]:
        """End-to-end review helper used by the CLI command."""

        bundle = self.collector.collect_pull_request_details(repo=repo, number=number)
        # Create target directory once at the start for better performance
        target_dir = self._ensure_target_dir(bundle.repo, bundle.number)

        # Write all review files
        artefact_path = target_dir / ARTEFACTS_FILENAME
        self._write_json(artefact_path, bundle.to_dict())

        summary = self.generate_summary(bundle)
        summary_path = target_dir / REVIEW_SUMMARY_FILENAME
        self._write_json(summary_path, summary.to_dict())

        markdown_path = target_dir / REVIEW_MARKDOWN_FILENAME
        lines: List[str] = []
        lines.extend(self._render_markdown_header(bundle))
        lines.extend(self._render_markdown_overview(summary))
        lines.extend(self._render_markdown_points("장점", summary.strengths))
        lines.extend(self._render_markdown_points("개선할 부분", summary.improvements))
        lines.extend(self._render_markdown_code_highlights(bundle))
        lines.extend(self._render_markdown_footer())

        try:
            markdown_path.write_text("\n".join(lines), encoding="utf-8")
        except (OSError, PermissionError) as exc:
            logger.error(f"Failed to write markdown to {markdown_path}: {exc}")
            raise

        return artefact_path, summary_path, markdown_path


__all__ = ["Reviewer"]
