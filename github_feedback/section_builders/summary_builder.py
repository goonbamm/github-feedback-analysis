"""Summary section builder."""

from typing import Any, List, Optional

from ..core.console import Console
from ..core.models import MetricSnapshot
from .base_builder import SectionBuilder

console = Console()


class SummaryBuilder(SectionBuilder):
    """Builder for header, summary overview, and summary table sections."""

    def __init__(self, metrics: MetricSnapshot, llm_client: Optional[Any] = None):
        """Initialize builder with metrics and optional LLM client.

        Args:
            metrics: MetricSnapshot containing all analysis data
            llm_client: Optional LLM client for generating summary quotes
        """
        super().__init__(metrics)
        self.llm_client = llm_client

    def build(self) -> List[str]:
        """Build complete summary section including header and overview table.

        Returns:
            List of markdown lines for summary section
        """
        lines = []
        lines.extend(self.build_header_and_summary())
        lines.extend(self.build_summary_overview_table())
        return lines

    def build_header_and_summary(self) -> List[str]:
        """Build header and summary section.

        Returns:
            List of markdown lines for header section
        """
        lines = ["# 🚀 GitHub Feedback Report", ""]

        # Generate witty summary quote if LLM client is available
        if self.llm_client and (self.metrics.awards or self.metrics.highlights or self.metrics.summary):
            try:
                quote = self.llm_client.generate_award_summary_quote(
                    self.metrics.awards,
                    self.metrics.highlights,
                    self.metrics.summary,
                )
                if quote:
                    lines.append(f"> ✨ **{quote}**")
                    lines.append("")
            except Exception as e:
                # Silently skip if quote generation fails
                console.log("Failed to generate award summary quote", f"error={e}")

        lines.append(f"**Repository**: {self.metrics.repo}")
        lines.append(f"**Period**: {self.metrics.months} months")

        if self.metrics.since_date and self.metrics.until_date:
            since_str = self.metrics.since_date.strftime("%Y-%m-%d")
            until_str = self.metrics.until_date.strftime("%Y-%m-%d")
            lines.append(f"**Analysis Period**: {since_str} ~ {until_str}")

        lines.append("")
        lines.append("---")
        lines.append("")

        return lines

    def build_summary_overview_table(self) -> List[str]:
        """Build integrated summary table with strengths, areas for improvement, and growth.

        Returns:
            List of markdown lines for summary overview table
        """
        lines = ["## 📊 한눈에 보는 요약", ""]
        lines.append("> 잘하고 있는 것, 보완하면 좋을 것, 성장한 점을 한눈에 확인하세요")
        lines.append("")

        lines.append("| 구분 | 내용 |")
        lines.append("|------|------|")

        # 1. 잘하고 있는 것 (Strengths) - from awards and highlights
        strengths = []

        # Get top awards (max 3)
        if self.metrics.awards:
            top_awards = self.metrics.awards[:3]
            strengths.extend([f"🏆 {award}" for award in top_awards])

        # Get key highlights if we need more (max 3 total)
        if len(strengths) < 3 and self.metrics.highlights:
            remaining = 3 - len(strengths)
            for highlight in self.metrics.highlights[:remaining]:
                # Shorten highlight to first sentence or 80 chars
                short_highlight = highlight.split('.')[0][:80]
                if len(highlight.split('.')[0]) > 80:
                    short_highlight += "..."
                strengths.append(f"✨ {short_highlight}")

        # Add strengths to table
        if strengths:
            strengths_text = "<br>".join(strengths)
            lines.append(f"| **✅ 잘하고 있는 것** | {strengths_text} |")
        else:
            lines.append("| **✅ 잘하고 있는 것** | 활동을 분석 중입니다 |")

        # 2. 보완하면 좋을 것 (Areas for Improvement) - from detailed feedback suggestions
        improvements = []

        if self.metrics.detailed_feedback:
            # Collect suggestions from all feedback types
            if self.metrics.detailed_feedback.commit_feedback and hasattr(self.metrics.detailed_feedback.commit_feedback, 'suggestions'):
                improvements.extend([f"📝 {s}" for s in self.metrics.detailed_feedback.commit_feedback.suggestions[:2]])

            if len(improvements) < 3 and self.metrics.detailed_feedback.pr_title_feedback and hasattr(self.metrics.detailed_feedback.pr_title_feedback, 'suggestions'):
                remaining = 3 - len(improvements)
                improvements.extend([f"🔀 {s}" for s in self.metrics.detailed_feedback.pr_title_feedback.suggestions[:remaining]])

            if len(improvements) < 3 and self.metrics.detailed_feedback.review_tone_feedback and hasattr(self.metrics.detailed_feedback.review_tone_feedback, 'suggestions'):
                remaining = 3 - len(improvements)
                improvements.extend([f"👀 {s}" for s in self.metrics.detailed_feedback.review_tone_feedback.suggestions[:remaining]])

        # Add improvement areas to table
        if improvements:
            improvements_text = "<br>".join(improvements[:3])
            lines.append(f"| **💡 보완하면 좋을 것** | {improvements_text} |")
        else:
            lines.append("| **💡 보완하면 좋을 것** | 전반적으로 좋은 품질을 유지하고 있습니다 |")

        # 3. 성장한 점 (Growth) - from retrospective and highlights
        growth_points = []

        # Get from retrospective if available
        if self.metrics.retrospective:
            # Use time comparisons showing positive growth
            if hasattr(self.metrics.retrospective, 'time_comparisons') and self.metrics.retrospective.time_comparisons:
                for tc in self.metrics.retrospective.time_comparisons[:2]:
                    if tc.direction == "increasing" and tc.significance in ["major", "moderate"]:
                        growth_points.append(f"📈 {tc.metric_name} {tc.change_percentage:+.0f}% 증가")

            # Use behavior patterns with positive impact
            if len(growth_points) < 3 and hasattr(self.metrics.retrospective, 'behavior_patterns') and self.metrics.retrospective.behavior_patterns:
                remaining = 3 - len(growth_points)
                positive_patterns = [bp for bp in self.metrics.retrospective.behavior_patterns if bp.impact == "positive"]
                for pattern in positive_patterns[:remaining]:
                    short_desc = pattern.description[:60]
                    if len(pattern.description) > 60:
                        short_desc += "..."
                    growth_points.append(f"🧠 {short_desc}")

        # Fallback to highlights
        if len(growth_points) < 3 and self.metrics.highlights:
            remaining = 3 - len(growth_points)
            for highlight in self.metrics.highlights[:remaining]:
                short_highlight = highlight.split('.')[0][:60]
                if len(highlight.split('.')[0]) > 60:
                    short_highlight += "..."
                growth_points.append(f"✨ {short_highlight}")

        # Add growth points to table
        if growth_points:
            growth_text = "<br>".join(growth_points[:3])
            lines.append(f"| **🌱 성장한 점** | {growth_text} |")
        else:
            lines.append("| **🌱 성장한 점** | 꾸준한 활동으로 성장하고 있습니다 |")

        lines.append("")
        lines.append("---")
        lines.append("")
        return lines
