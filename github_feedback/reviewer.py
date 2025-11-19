"""Pull request review orchestration for GitHub feedback analysis."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

import requests

from .collector import Collector
from .console import Console
from .constants import HEURISTIC_THRESHOLDS, TEXT_LIMITS
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
    llm: Optional[LLMClient] = None
    output_dir: Path = Path("reports/reviews")

    def _target_dir(self, repo: str, number: int) -> Path:
        safe_repo = repo.replace("/", "__")
        return self.output_dir / safe_repo / f"pr-{number}"

    def _ensure_target_dir(self, repo: str, number: int) -> Path:
        """Create and return the target directory for PR review files."""
        from .utils import FileSystemManager

        target_dir = self._target_dir(repo, number)
        return FileSystemManager.ensure_directory(target_dir)

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

    def _evaluate_description(
        self, bundle: PullRequestReviewBundle
    ) -> Tuple[List[ReviewPoint], List[ReviewPoint]]:
        """Create review points about the PR description quality."""

        strengths: List[ReviewPoint] = []
        improvements: List[ReviewPoint] = []
        min_quality_len = HEURISTIC_THRESHOLDS["pr_body_min_quality_length"]
        body = bundle.body.strip() if bundle.body else ""

        if body and len(body) > min_quality_len:
            strengths.append(
                ReviewPoint(
                    message="Pull Request 설명이 상세하고 맥락을 잘 제공합니다.",
                    example=body.splitlines()[0][
                        : TEXT_LIMITS["commit_message_display_length"]
                    ],
                )
            )
        elif body:
            improvements.append(
                ReviewPoint(
                    message="PR 설명이 너무 간략합니다. 더 많은 맥락을 제공해보세요.",
                    example="변경 이유, 영향 범위, 테스트 방법 등을 포함하세요.",
                )
            )
        else:
            improvements.append(
                ReviewPoint(
                    message="PR 설명이 없습니다. 리뷰어를 위해 변경사항을 설명해주세요.",
                    example="무엇을, 왜, 어떻게 변경했는지 설명이 필요합니다.",
                )
            )

        return strengths, improvements

    def _evaluate_tests(
        self, bundle: PullRequestReviewBundle
    ) -> Tuple[List[ReviewPoint], List[ReviewPoint]]:
        """Assess whether the PR adds or updates tests."""

        strengths: List[ReviewPoint] = []
        improvements: List[ReviewPoint] = []
        test_files = [
            f
            for f in bundle.files
            if "test" in f.filename.lower() or "spec" in f.filename.lower()
        ]

        if test_files:
            strengths.append(
                ReviewPoint(
                    message=f"테스트 파일이 포함되어 있습니다 ({len(test_files)}개).",
                    example=", ".join([f.filename for f in test_files[:3]]),
                )
            )
        else:
            improvements.append(
                ReviewPoint(
                    message="테스트 파일이 감지되지 않았습니다.",
                    example="변경사항에 대한 테스트 추가를 고려해보세요.",
                )
            )

        return strengths, improvements

    def _evaluate_pr_size(
        self, bundle: PullRequestReviewBundle
    ) -> Tuple[List[ReviewPoint], List[ReviewPoint]]:
        """Assess the size of a PR in terms of total changes."""

        strengths: List[ReviewPoint] = []
        improvements: List[ReviewPoint] = []
        pr_very_large = HEURISTIC_THRESHOLDS["pr_very_large"]
        pr_small = HEURISTIC_THRESHOLDS["pr_small"]
        total_changes = bundle.additions + bundle.deletions

        if total_changes > pr_very_large:
            improvements.append(
                ReviewPoint(
                    message=f"PR이 매우 큽니다 ({total_changes}줄 변경).",
                    example="리뷰를 쉽게 하기 위해 작은 PR로 나누는 것을 고려해보세요.",
                )
            )
        elif total_changes < pr_small:
            strengths.append(
                ReviewPoint(
                    message=f"적절한 크기의 PR입니다 ({total_changes}줄 변경).",
                    example="작은 PR은 리뷰하기 쉽고 머지 충돌이 적습니다.",
                )
            )

        return strengths, improvements

    def _evaluate_documentation(
        self, bundle: PullRequestReviewBundle
    ) -> Tuple[List[ReviewPoint], List[ReviewPoint]]:
        """Highlight documentation changes, if any."""

        strengths: List[ReviewPoint] = []
        improvements: List[ReviewPoint] = []
        doc_files = [
            f
            for f in bundle.files
            if any(ext in f.filename.lower() for ext in [".md", "readme", "doc"])
        ]

        if doc_files:
            strengths.append(
                ReviewPoint(
                    message="문서 업데이트가 포함되어 있습니다.",
                    example=", ".join([f.filename for f in doc_files[:2]]),
                )
            )

        return strengths, improvements

    def _evaluate_self_review(
        self, bundle: PullRequestReviewBundle
    ) -> Tuple[List[ReviewPoint], List[ReviewPoint]]:
        """Assess whether self-review comments were provided."""

        strengths: List[ReviewPoint] = []
        improvements: List[ReviewPoint] = []

        if bundle.review_comments and len(bundle.review_comments) > 0:
            strengths.append(
                ReviewPoint(
                    message=f"셀프 리뷰 코멘트가 있습니다 ({len(bundle.review_comments)}개).",
                    example="리뷰어에게 도움이 되는 코멘트를 제공했습니다.",
                )
            )
        else:
            improvements.append(
                ReviewPoint(
                    message="셀프 리뷰 코멘트를 추가하는 것을 고려해보세요.",
                    example="복잡한 로직이나 주요 결정사항에 대해 설명하세요.",
                )
            )

        return strengths, improvements

    def _fallback_summary(self, bundle: PullRequestReviewBundle) -> ReviewSummary:
        """Provide a deterministic summary with heuristic analysis when the LLM cannot be reached."""

        overview = (
            f"Pull Request #{bundle.number}는 {bundle.changed_files}개 파일을 수정했으며, "
            f"+{bundle.additions} 추가, -{bundle.deletions} 삭제가 있습니다."
        )

        strengths: List[ReviewPoint] = []
        improvements: List[ReviewPoint] = []

        evaluators = [
            self._evaluate_description,
            self._evaluate_tests,
            self._evaluate_pr_size,
            self._evaluate_documentation,
            self._evaluate_self_review,
        ]

        for evaluator in evaluators:
            new_strengths, new_improvements = evaluator(bundle)
            strengths.extend(new_strengths)
            improvements.extend(new_improvements)

        # Ensure we have at least some content
        if not strengths:
            strengths.append(
                ReviewPoint(
                    message="변경사항이 제출되었습니다.",
                    example=f"{bundle.changed_files}개 파일에 걸친 변경사항.",
                )
            )

        return ReviewSummary(overview=overview, strengths=strengths, improvements=improvements)

    def _handle_llm_error(
        self, bundle: PullRequestReviewBundle, exc: Exception, message: str
    ) -> ReviewSummary:
        """Handle LLM errors with logging and fallback.

        Args:
            bundle: Pull request data bundle
            exc: Exception that occurred
            message: User-friendly error message

        Returns:
            Fallback summary
        """
        logger.error(f"LLM error for PR #{bundle.number}: {exc}")
        console.log(f"[warning]{message}[/]")
        return self._fallback_summary(bundle)

    def generate_summary(self, bundle: PullRequestReviewBundle) -> ReviewSummary:
        """Request LLM feedback while falling back gracefully when required."""

        if not self.llm:
            console.log("LLM client not configured; using fallback summary")
            return self._fallback_summary(bundle)

        try:
            summary = self.llm.generate_review(bundle)
        except requests.HTTPError as exc:  # pragma: no cover - network errors are hard to simulate
            status_code = exc.response.status_code if exc.response else 'unknown'
            # Distinguish between retryable and permanent errors
            error_type = "Client error" if exc.response and exc.response.status_code in {400, 401, 403, 404, 422} else "Server error"
            message = f"LLM request failed (HTTP {status_code}): {error_type}, using fallback"
            summary = self._handle_llm_error(bundle, exc, message)
        except requests.ConnectionError as exc:
            summary = self._handle_llm_error(bundle, exc, "Cannot connect to LLM server, using fallback summary")
        except requests.Timeout as exc:
            summary = self._handle_llm_error(bundle, exc, "LLM request timed out, using fallback summary")
        except json.JSONDecodeError as exc:
            summary = self._handle_llm_error(bundle, exc, "LLM returned invalid JSON, using fallback summary")
        except ValueError as exc:
            summary = self._handle_llm_error(bundle, exc, f"LLM response validation failed: {exc}, using fallback")
        except KeyError as exc:
            summary = self._handle_llm_error(bundle, exc, f"LLM response incomplete (missing {exc}), using fallback")

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

    def _build_markdown_content(
        self, bundle: PullRequestReviewBundle, summary: ReviewSummary
    ) -> List[str]:
        """Build complete markdown content for review.

        Args:
            bundle: Pull request data bundle
            summary: Review summary with strengths and improvements

        Returns:
            List of markdown lines
        """
        lines: List[str] = []
        lines.extend(self._render_markdown_header(bundle))
        lines.extend(self._render_markdown_overview(summary))
        lines.extend(self._render_markdown_points("장점", summary.strengths))
        lines.extend(self._render_markdown_points("개선할 부분", summary.improvements))
        lines.extend(self._render_markdown_code_highlights(bundle))
        lines.extend(self._render_markdown_footer())
        return lines

    def create_markdown(
        self, bundle: PullRequestReviewBundle, summary: ReviewSummary
    ) -> Path:
        """Create a high readability markdown review with generous spacing."""

        target_dir = self._ensure_target_dir(bundle.repo, bundle.number)
        markdown_path = target_dir / REVIEW_MARKDOWN_FILENAME

        lines = self._build_markdown_content(bundle, summary)

        try:
            markdown_path.write_text("\n".join(lines), encoding="utf-8")
        except (OSError, PermissionError) as exc:
            logger.error(f"Failed to write markdown to {markdown_path}: {exc}")
            raise
        return markdown_path

    def review_pull_request(
        self,
        repo: str,
        number: int,
        force_refresh: bool = False
    ) -> tuple[Path, Path, Path]:
        """End-to-end review helper used by the CLI command.

        Args:
            repo: Repository name in owner/repo format
            number: Pull request number
            force_refresh: If True, regenerate review even if cached version exists

        Returns:
            Tuple of (artefact_path, summary_path, markdown_path)
        """

        # Check if cached review exists
        target_dir = self._target_dir(repo, number)
        artefact_path = target_dir / ARTEFACTS_FILENAME
        summary_path = target_dir / REVIEW_SUMMARY_FILENAME
        markdown_path = target_dir / REVIEW_MARKDOWN_FILENAME

        # Return cached results if all files exist and force_refresh is False
        if not force_refresh and all(p.exists() for p in [artefact_path, summary_path, markdown_path]):
            logger.info(f"Using cached review for PR #{number} from {target_dir}")
            return artefact_path, summary_path, markdown_path

        # Generate new review
        logger.info(f"Generating new review for PR #{number}")
        bundle = self.collector.collect_pull_request_details(repo=repo, number=number)

        # Create target directory once at the start for better performance
        target_dir = self._ensure_target_dir(bundle.repo, bundle.number)

        # Write all review files
        artefact_path = self.persist_bundle(bundle)

        summary = self.generate_summary(bundle)
        summary_path = self.persist_summary(bundle, summary)

        markdown_path = self.create_markdown(bundle, summary)

        return artefact_path, summary_path, markdown_path


__all__ = ["Reviewer"]
