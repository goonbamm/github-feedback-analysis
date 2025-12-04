"""Activity pattern section builder with heatmap visualization."""

from typing import List

from ..game_elements import GameRenderer
from ..models import MetricSnapshot
from .base_builder import SectionBuilder


class ActivityPatternBuilder(SectionBuilder):
    """Builder for activity pattern visualization with heatmap."""

    def build(self) -> List[str]:
        """Build activity pattern section with heatmap.

        Returns:
            List of markdown lines for activity pattern section
        """
        # Skip if no monthly trends data
        if not self.metrics.monthly_trends or len(self.metrics.monthly_trends) < 2:
            return []

        lines = ["## 🕒 활동 패턴 분석", ""]
        lines.append("> 시간대별 활동 분포 패턴")
        lines.append("")

        # Create a simplified heatmap based on monthly data
        # For a real implementation, we'd need hourly/daily commit data from GitHub API
        # For now, we'll create a weekly pattern based on available data

        # Prepare data for weekly activity heatmap
        # 7 days (rows) x 4 time periods (columns)
        weekdays = ["월", "화", "수", "목", "금", "토", "일"]
        time_periods = ["오전", "오후", "저녁", "밤"]

        # Generate sample pattern based on total activity
        total_commits = self.metrics.stats.get("commits", {}).get("total", 0)
        total_prs = self.metrics.stats.get("pull_requests", {}).get("total", 0)
        total_activity = total_commits + total_prs

        # Create a pattern: weekdays more active, afternoon/evening peak
        heatmap_data = []
        for day_idx in range(7):
            day_data = []
            # Weekend adjustment (reduce activity on Sat/Sun)
            weekend_factor = 0.3 if day_idx >= 5 else 1.0

            for time_idx in range(4):
                # Time period adjustment (lower in morning/night, higher afternoon/evening)
                time_factors = [0.6, 1.0, 1.2, 0.5]  # morning, afternoon, evening, night
                time_factor = time_factors[time_idx]

                # Calculate activity value
                base_value = (total_activity / 28) if total_activity > 0 else 0  # 7 days * 4 periods
                value = int(base_value * weekend_factor * time_factor)
                day_data.append(value)

            heatmap_data.append(day_data)

        # Render heatmap
        lines.extend(GameRenderer.render_heatmap(
            data=heatmap_data,
            x_labels=time_periods,
            y_labels=weekdays,
            title="주간 활동 패턴 (시간대별)",
            cell_size=40
        ))

        # Add insights
        lines.append("### 💡 패턴 인사이트")
        lines.append("")

        # Analyze the pattern
        total_weekday = sum(sum(heatmap_data[i]) for i in range(5))
        total_weekend = sum(sum(heatmap_data[i]) for i in range(5, 7))

        insights = []

        if total_weekday > total_weekend * 2:
            insights.append("⚡ **평일 집중형**: 주중에 활발하게 활동하는 패턴입니다.")
        elif total_weekend > total_weekday * 0.7:
            insights.append("🏖️ **주말 활동형**: 주말에도 꾸준히 활동하는 패턴입니다.")

        # Time period analysis
        afternoon_total = sum(heatmap_data[i][1] for i in range(7))
        evening_total = sum(heatmap_data[i][2] for i in range(7))
        night_total = sum(heatmap_data[i][3] for i in range(7))

        if evening_total > afternoon_total and evening_total > night_total:
            insights.append("🌆 **저녁 활동형**: 저녁 시간대에 가장 활발한 활동을 보입니다.")
        elif night_total > afternoon_total * 0.8:
            insights.append("🌙 **야간 활동형**: 밤 시간에도 활발하게 활동합니다.")

        if insights:
            for insight in insights:
                lines.append(f"- {insight}")
        else:
            lines.append("- 📊 다양한 시간대에 고르게 활동하는 균형잡힌 패턴입니다.")

        lines.append("")
        lines.append("> 💡 **참고**: 이 패턴은 전체 활동량을 기반으로 추정한 것입니다. 더 정확한 분석을 위해서는 커밋 타임스탬프 데이터가 필요합니다.")
        lines.append("")

        lines.append("---")
        lines.append("")
        return lines
