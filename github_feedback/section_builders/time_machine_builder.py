"""Time machine section builder for past vs present comparison."""

from __future__ import annotations

from typing import List

from github_feedback.core.models import MetricSnapshot

from .base_builder import SectionBuilder


class TimeMachineBuilder(SectionBuilder):
    """Builder for time machine comparison section."""

    def build(self) -> List[str]:
        """Build the time machine comparison section."""
        if not self.metrics.time_machine:
            return []

        tm = self.metrics.time_machine
        lines = []

        lines.append("## ⏰ 타임머신: 과거 vs 현재")
        lines.append("")
        lines.append(f"**{tm.past_period_label}** 대비 **{tm.present_period_label}** 비교")
        lines.append("")

        # Overall summary
        lines.append(f"### {tm.overall_growth_summary}")
        lines.append("")

        # Comparison table
        lines.append("| 지표 | 과거 | 현재 | 변화 | 트렌드 |")
        lines.append("|------|------|------|------|--------|")

        for comp in tm.comparisons:
            trend_icon = self._get_trend_icon(comp.trend)
            change_str = f"{comp.change_percent:+.1f}%"

            lines.append(
                f"| {comp.metric_name} | {comp.past_value:.1f} | {comp.present_value:.1f} | {change_str} | {trend_icon} |"
            )

        lines.append("")

        # Key insights
        lines.append("### 🔍 주요 인사이트")
        lines.append("")
        lines.append(f"**🏆 가장 큰 성장:** {tm.biggest_improvement}")
        lines.append("")
        lines.append(f"**💡 주의 필요:** {tm.needs_attention}")
        lines.append("")

        # Detailed insights for each comparison
        lines.append("### 📊 상세 분석")
        lines.append("")

        for comp in tm.comparisons:
            if comp.insight:
                lines.append(f"- **{comp.metric_name}:** {comp.insight}")

        lines.append("")

        return lines

    def _get_trend_icon(self, trend: str) -> str:
        """Get icon for trend."""
        if trend == "improving":
            return "📈 상승"
        elif trend == "declining":
            return "📉 하락"
        else:
            return "➡️ 유지"
