"""Streak section builder for contribution consistency visualization."""

from __future__ import annotations

from typing import List

from github_feedback.game_elements import GameRenderer
from github_feedback.core.models import MetricSnapshot

from .base_builder import SectionBuilder


class StreakBuilder(SectionBuilder):
    """Builder for streak and calendar heatmap section."""

    def build(self) -> List[str]:
        """Build the streak section with calendar heatmap."""
        if not self.metrics.streak_data:
            return []

        streak = self.metrics.streak_data
        lines = []

        lines.append("## 🔥 기여 스트릭 & 활동 캘린더")
        lines.append("")

        # Streak overview cards
        lines.append('<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin: 20px 0;">')

        # Current streak card
        lines.append(self._render_streak_card(
            "🔥 현재 스트릭",
            str(streak.current_streak),
            f"{streak.current_streak}일 연속 기여!",
            "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)"
        ))

        # Longest streak card
        lines.append(self._render_streak_card(
            "⭐ 최장 스트릭",
            str(streak.longest_streak),
            f"역대 최고 기록",
            "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)"
        ))

        # Total active days card
        lines.append(self._render_streak_card(
            "📅 활동일 수",
            str(streak.total_active_days),
            f"총 기여한 날",
            "linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)"
        ))

        lines.append('</div>')
        lines.append("")

        # Streak badges
        if streak.streak_badges:
            lines.append("### 🏆 스트릭 배지")
            lines.append("")
            lines.append('<div style="display: flex; flex-wrap: wrap; gap: 8px; margin: 16px 0;">')
            for badge in streak.streak_badges:
                lines.append(self._render_badge(badge))
            lines.append('</div>')
            lines.append("")

        # Calendar heatmap
        if streak.daily_contributions:
            lines.append("### 📊 활동 히트맵")
            lines.append("")
            lines.append(self._render_heatmap(streak.daily_contributions))
            lines.append("")

        # Insights
        lines.append("### 💡 스트릭 인사이트")
        lines.append("")
        lines.append(self._generate_streak_insights(streak))
        lines.append("")

        return lines

    def _render_streak_card(
        self,
        title: str,
        value: str,
        subtitle: str,
        gradient: str
    ) -> str:
        """Render a streak stat card."""
        return f'''<div style="background: {gradient}; border-radius: 12px; padding: 20px; color: white; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
    <div style="font-size: 14px; opacity: 0.9; margin-bottom: 8px;">{title}</div>
    <div style="font-size: 36px; font-weight: bold; margin-bottom: 4px;">{value}</div>
    <div style="font-size: 12px; opacity: 0.8;">{subtitle}</div>
</div>'''

    def _render_badge(self, badge_text: str) -> str:
        """Render a streak badge."""
        return f'<span style="display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 8px 16px; border-radius: 20px; font-size: 14px; font-weight: 500; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">{badge_text}</span>'

    def _render_heatmap(self, daily_contributions: dict) -> str:
        """Render a GitHub-style contribution heatmap.

        Args:
            daily_contributions: Dict mapping date strings to contribution counts

        Returns:
            HTML string with heatmap visualization
        """
        if not daily_contributions:
            return ""

        lines = []
        lines.append('<div style="background: #f6f8fa; border-radius: 8px; padding: 16px; overflow-x: auto;">')
        lines.append('<div style="font-size: 12px; color: #586069; margin-bottom: 8px;">일별 기여 활동</div>')

        # Sort dates
        sorted_dates = sorted(daily_contributions.keys())

        # Group by weeks
        weeks = []
        current_week = []

        for date_str in sorted_dates:
            if len(current_week) == 7:
                weeks.append(current_week)
                current_week = []
            current_week.append((date_str, daily_contributions[date_str]))

        if current_week:
            weeks.append(current_week)

        # Render heatmap grid
        lines.append('<div style="display: grid; grid-template-columns: repeat(auto-fill, 12px); gap: 3px; max-width: 800px;">')

        max_contributions = max(daily_contributions.values()) if daily_contributions else 1

        for week in weeks:
            for date_str, count in week:
                color = self._get_heatmap_color(count, max_contributions)
                title = f"{date_str}: {count} contributions"
                lines.append(
                    f'<div title="{title}" style="width: 12px; height: 12px; background: {color}; border-radius: 2px;"></div>'
                )

        lines.append('</div>')

        # Legend
        lines.append('<div style="display: flex; align-items: center; gap: 4px; margin-top: 12px; font-size: 11px; color: #586069;">')
        lines.append('<span>Less</span>')
        for i in range(5):
            color = self._get_heatmap_color(i, 4)
            lines.append(f'<div style="width: 12px; height: 12px; background: {color}; border-radius: 2px;"></div>')
        lines.append('<span>More</span>')
        lines.append('</div>')

        lines.append('</div>')

        return "\n".join(lines)

    def _get_heatmap_color(self, count: int, max_count: int) -> str:
        """Get color for heatmap cell based on contribution count.

        Args:
            count: Contribution count
            max_count: Maximum contribution count

        Returns:
            CSS color string
        """
        if count == 0:
            return "#ebedf0"

        # Calculate intensity (0-4 scale like GitHub)
        if max_count == 0:
            intensity = 0
        else:
            ratio = count / max_count
            if ratio <= 0.25:
                intensity = 1
            elif ratio <= 0.5:
                intensity = 2
            elif ratio <= 0.75:
                intensity = 3
            else:
                intensity = 4

        colors = {
            0: "#ebedf0",
            1: "#9be9a8",
            2: "#40c463",
            3: "#30a14e",
            4: "#216e39",
        }

        return colors.get(intensity, "#ebedf0")

    def _generate_streak_insights(self, streak) -> str:
        """Generate insights about streak patterns."""
        insights = []

        if streak.current_streak >= 30:
            insights.append("🔥 **놀라운 일관성!** 30일 이상 연속으로 기여하고 계십니다. 이런 꾸준함이 성장의 비결입니다!")
        elif streak.current_streak >= 14:
            insights.append("👏 **훌륭한 습관!** 2주 이상 연속 기여는 쉽지 않은 일입니다. 계속 이어가세요!")
        elif streak.current_streak >= 7:
            insights.append("💪 **좋은 시작!** 일주일 연속 기여를 달성했습니다. 이제 습관이 되어가고 있어요!")
        elif streak.current_streak > 0:
            insights.append(f"🌱 **현재 {streak.current_streak}일 스트릭!** 꾸준함은 힘입니다. 계속 이어나가세요!")
        else:
            insights.append("💡 **새로운 시작!** 오늘부터 스트릭을 시작해보세요. 작은 기여도 의미있습니다!")

        if streak.longest_streak > streak.current_streak + 7:
            insights.append(f"📈 **이전 최고 기록은 {streak.longest_streak}일!** 다시 그 기록에 도전해보세요!")

        # Activity density
        if streak.daily_contributions:
            total_days = len(streak.daily_contributions)
            active_ratio = streak.total_active_days / total_days if total_days > 0 else 0

            if active_ratio >= 0.5:
                insights.append(f"⭐ **고밀도 활동!** 전체 기간의 {active_ratio*100:.0f}%에 기여했습니다!")
            elif active_ratio >= 0.3:
                insights.append(f"👍 **안정적 활동!** 전체 기간의 {active_ratio*100:.0f}%에 기여했습니다!")

        return "\n\n".join(insights) if insights else "계속해서 기여를 이어가세요!"
