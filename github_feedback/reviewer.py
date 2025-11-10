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

console = Console()


def _truncate_patch(patch: str, max_lines: int = 12) -> str:
    """Trim diff content to a manageable snippet."""

    lines = patch.splitlines()
    if len(lines) <= max_lines:
        return patch
    head = lines[: max_lines - 1]
    head.append("...")
    return "\n".join(head)


@dataclass(slots=True)
class Reviewer:
    """Coordinate pull request data collection and LLM review generation."""

    collector: Collector
    llm: LLMClient | None = None
    output_dir: Path = Path("reports/reviews")

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
            f"Pull request #{bundle.number} updates {bundle.changed_files} files with "
            f"+{bundle.additions} additions and -{bundle.deletions} deletions."
        )

        strengths: List[ReviewPoint] = []
        if bundle.body.strip():
            strengths.append(
                ReviewPoint(
                    message="The pull request description outlines the intent clearly.",
                    example=bundle.body.strip().splitlines()[0],
                )
            )
        if bundle.files:
            first_file = bundle.files[0]
            strengths.append(
                ReviewPoint(
                    message=f"Includes focused changes in `{first_file.filename}`.",
                    example=_truncate_patch(first_file.patch or ""),
                )
            )

        improvements: List[ReviewPoint] = []
        if not bundle.review_comments:
            improvements.append(
                ReviewPoint(
                    message="Consider adding self-review comments to guide reviewers.",
                    example="No inline comments were provided in the pull request.",
                )
            )
        if bundle.files:
            improvements.append(
                ReviewPoint(
                    message="Double-check whether regression tests are affected.",
                    example=f"Review the changes in `{bundle.files[-1].filename}` for coverage gaps.",
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
                f"Pull request #{bundle.number} spans {bundle.changed_files} files "
                f"with {bundle.additions} additions and {bundle.deletions} deletions."
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
        lines.append("# Pull Request Review")
        lines.append("")
        lines.append(f"Repository : **{bundle.repo}**")
        lines.append(f"Pull Request : **#{bundle.number} {bundle.title}**")
        lines.append("")
        lines.append(f"Author : **{bundle.author or 'unknown'}**")
        lines.append(f"URL : {bundle.html_url}")
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("## Overview")
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
                    lines.append(f"  _Example:_ {point.example}")
                    lines.append("")
                else:
                    lines.append("")
            if not has_points:
                lines.append("- No items recorded.")
                lines.append("")

        _render_points("Strengths", summary.strengths)
        _render_points("Areas To Improve", summary.improvements)

        lines.append("## Code Highlights")
        lines.append("")
        if not bundle.files:
            lines.append("- No file changes were detected.")
        else:
            for file in bundle.files[:5]:
                lines.append(
                    f"- `{file.filename}` — {file.changes} changes ( +{file.additions} / -{file.deletions} )"
                )
                if file.patch:
                    lines.append("")
                    lines.append("  ```diff")
                    lines.append(_truncate_patch(file.patch))
                    lines.append("  ```")
                    lines.append("")
                else:
                    lines.append("")

        lines.append("")
        lines.append("## Stored Artefacts")
        lines.append("")
        lines.append("- `artefacts.json` contains the raw pull request data.")
        lines.append("- `review_summary.json` preserves the structured LLM response.")
        lines.append("")

        markdown_path.write_text("\n".join(lines), encoding="utf-8")
        return markdown_path

    def review_pull_request(self, repo: str, number: int) -> tuple[Path, Path, Path]:
        """End-to-end review helper used by the CLI command."""

        bundle = self.collector.collect_pull_request_details(repo=repo, number=number)
        artefact_path = self.persist_bundle(bundle)
        summary = self.generate_summary(bundle)
        summary_path = self.persist_summary(bundle, summary)
        markdown_path = self.create_markdown(bundle, summary)
        return artefact_path, summary_path, markdown_path


__all__ = ["Reviewer"]
