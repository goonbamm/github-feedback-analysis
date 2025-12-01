"""Report generation for GitHub feedback analysis."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from .console import Console
from .feedback_builders import FeedbackBuilder
from .models import MetricSnapshot
from .retrospective_builders import RetrospectiveBuilder
from .section_builders.awards_builder import AwardsBuilder
from .section_builders.character_stats_builder import CharacterStatsBuilder
from .section_builders.highlights_builder import HighlightsBuilder
from .section_builders.monthly_trends_builder import MonthlyTrendsBuilder
from .section_builders.skill_tree_builder import SkillTreeBuilder
from .section_builders.spotlight_builder import SpotlightBuilder
from .section_builders.summary_builder import SummaryBuilder
from .section_builders.tech_stack_builder import TechStackBuilder
from .section_builders.witch_critique_builder import WitchCritiqueBuilder

console = Console()


@dataclass(slots=True)
class Reporter:
    """Create human-readable artefacts from metrics."""

    output_dir: Path = Path("reports")
    _current_repo: Optional[str] = None  # Temporary storage for current repo during report generation
    llm_client: Optional[Any] = None  # Optional LLM client for generating summary quotes
    web_url: str = "https://github.com"  # Base URL for GitHub links (configurable for enterprise)

    def ensure_structure(self) -> None:
        from .utils import FileSystemManager

        FileSystemManager.ensure_directory(self.output_dir)

    def _get_repo_from_context(self) -> str:
        """Get the current repository being processed.

        Returns:
            Repository in 'owner/repo' format, or empty string if not available
        """
        return self._current_repo or ""

    def generate_markdown(self, metrics: MetricSnapshot) -> Path:
        """Create a markdown report for the provided metrics.

        Improved report structure for better user experience:
        1. Header with basic info
        2. Summary Overview Table - Quick glance at strengths, improvements, and growth
        3. Character Stats - Gamified visualization of repository metrics
        4. Awards Cabinet to celebrate achievements
        5. Growth Highlights to show progress
        6. Monthly Trends for pattern analysis
        7. Detailed Feedback for actionable insights
        8. Deep Retrospective for comprehensive analysis
        9. Spotlight Examples for concrete evidence
        10. Tech Stack to show technical breadth
        """
        self.ensure_structure()
        report_path = self.output_dir / "report.md"

        # Store repo for use in link generation
        self._current_repo = metrics.repo

        console.log("Writing markdown report", f"path={report_path}")

        # Add font styles at the beginning
        font_styles = [
            '<style>',
            '  @import url("https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&display=swap");',
            '  * {',
            '    font-family: "Noto Sans KR", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;',
            '  }',
            '</style>',
            ''
        ]

        # Build all sections using the new builders
        sections = [
            # 1. Header with basic info & Summary Overview Table
            SummaryBuilder(metrics, self.llm_client).build(),
            # 2. Character Stats - Gamified visualization
            CharacterStatsBuilder(metrics).build(),
            # 3. Skill Tree - Game-style skill representation
            SkillTreeBuilder(metrics).build(),
            # 4. Awards Cabinet - Celebrate achievements first!
            AwardsBuilder(metrics).build(),
            # 5. Growth Highlights - Show the story
            HighlightsBuilder(metrics).build(),
            # 6. Monthly Trends - Show patterns
            MonthlyTrendsBuilder(metrics).build(),
            # 7. Detailed Feedback - Actionable insights
            FeedbackBuilder(metrics, self.web_url).build(),
            # 8. Deep Retrospective - Comprehensive analysis
            RetrospectiveBuilder(metrics).build(),
            # 9. Witch's Critique - Harsh but constructive feedback
            WitchCritiqueBuilder(metrics).build(),
            # 10. Spotlight Examples - Concrete evidence
            SpotlightBuilder(metrics).build(),
            # 11. Tech Stack - Technical breadth
            TechStackBuilder(metrics).build(),
        ]

        # Combine all sections
        all_lines = []
        all_lines.extend(font_styles)  # Add font styles first
        for section in sections:
            all_lines.extend(section)

        try:
            report_path.write_text("\n".join(all_lines), encoding="utf-8")
        except (IOError, OSError) as e:
            raise IOError(f"Failed to write report to {report_path}: {e}") from e

        return report_path

    def generate_markdown_content(self, metrics: MetricSnapshot) -> str:
        """Generate markdown report content without writing to file.

        This is useful for in-memory report generation without creating files.

        Args:
            metrics: Metrics snapshot to generate report from

        Returns:
            Markdown report content as a string
        """
        # Store repo for use in link generation
        self._current_repo = metrics.repo

        # Add font styles at the beginning
        font_styles = [
            '<style>',
            '  @import url("https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&display=swap");',
            '  * {',
            '    font-family: "Noto Sans KR", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;',
            '  }',
            '</style>',
            ''
        ]

        # Build all sections using the new builders (same as generate_markdown)
        sections = [
            # 1. Header with basic info & Summary Overview Table
            SummaryBuilder(metrics, self.llm_client).build(),
            # 2. Character Stats - Gamified visualization
            CharacterStatsBuilder(metrics).build(),
            # 3. Skill Tree - Game-style skill representation
            SkillTreeBuilder(metrics).build(),
            # 4. Awards Cabinet - Celebrate achievements first!
            AwardsBuilder(metrics).build(),
            # 5. Growth Highlights - Show the story
            HighlightsBuilder(metrics).build(),
            # 6. Monthly Trends - Show patterns
            MonthlyTrendsBuilder(metrics).build(),
            # 7. Detailed Feedback - Actionable insights
            FeedbackBuilder(metrics, self.web_url).build(),
            # 8. Deep Retrospective - Comprehensive analysis
            RetrospectiveBuilder(metrics).build(),
            # 9. Witch's Critique - Harsh but constructive feedback
            WitchCritiqueBuilder(metrics).build(),
            # 10. Spotlight Examples - Concrete evidence
            SpotlightBuilder(metrics).build(),
            # 11. Tech Stack - Technical breadth
            TechStackBuilder(metrics).build(),
        ]

        # Combine all sections
        all_lines = []
        all_lines.extend(font_styles)  # Add font styles first
        for section in sections:
            all_lines.extend(section)

        return "\n".join(all_lines)
