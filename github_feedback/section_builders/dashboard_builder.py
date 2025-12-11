"""Dashboard cards section builder."""

from typing import Dict, List, Optional, Tuple

from ..game_elements import COLOR_PALETTE, GameRenderer
from ..core.models import MetricSnapshot
from .base_builder import SectionBuilder


class DashboardBuilder(SectionBuilder):
    """Builder for dashboard cards with key metrics summary."""

    def build(self) -> List[str]:
        """Build dashboard cards section with key metrics.

        Returns:
            List of markdown lines for dashboard section
        """
        lines = ["## 📊 핵심 지표 대시보드", ""]
        lines.append("> 한눈에 보는 주요 활동 지표")
        lines.append("")

        # Calculate key metrics
        stats = self.metrics.stats
        commits_data = stats.get("commits", {})
        prs_data = stats.get("pull_requests", {})
        reviews_data = stats.get("reviews", {})

        total_commits = commits_data.get("total", 0)
        total_prs = prs_data.get("total", 0)
        merged_prs = prs_data.get("merged", 0)
        total_reviews = reviews_data.get("total", 0)

        # Calculate merge rate
        merge_rate = (merged_prs / total_prs * 100) if total_prs > 0 else 0

        # Calculate monthly velocity
        months = self.metrics.months if self.metrics.months > 0 else 1
        monthly_commits = total_commits / months
        monthly_prs = total_prs / months

        # Get trend data if available from retrospective
        commit_trend = self._get_metric_trend("commits")
        pr_trend = self._get_metric_trend("pull_requests")
        review_trend = self._get_metric_trend("reviews")

        # Build metric cards data
        cards = [
            {
                "title": "총 커밋",
                "value": str(total_commits),
                "subtitle": f"월평균 {monthly_commits:.1f}개",
                "icon": "📝",
                "trend": commit_trend,
                "color": COLOR_PALETTE["info"]
            },
            {
                "title": "Pull Requests",
                "value": str(total_prs),
                "subtitle": f"월평균 {monthly_prs:.1f}개",
                "icon": "🔀",
                "trend": pr_trend,
                "color": COLOR_PALETTE["purple"]
            },
            {
                "title": "병합률",
                "value": f"{merge_rate:.1f}%",
                "subtitle": f"{merged_prs}/{total_prs} 병합됨",
                "icon": "✅",
                "trend": None,  # No trend for rate
                "color": COLOR_PALETTE["success"]
            },
            {
                "title": "코드 리뷰",
                "value": str(total_reviews),
                "subtitle": f"월평균 {total_reviews/months:.1f}개",
                "icon": "👀",
                "trend": review_trend,
                "color": COLOR_PALETTE["warning"]
            }
        ]

        # Render cards using HTML
        lines.extend(self._render_metric_cards(cards))

        lines.append("---")
        lines.append("")
        return lines

    def _get_metric_trend(self, metric_name: str) -> Optional[Tuple[str, str]]:
        """Get trend indicator for a metric.

        Args:
            metric_name: Name of the metric to check

        Returns:
            Tuple of (direction, percentage) or None if no trend data
        """
        if not self.metrics.retrospective:
            return None

        if not hasattr(self.metrics.retrospective, 'time_comparisons'):
            return None

        # Find matching time comparison
        for tc in self.metrics.retrospective.time_comparisons:
            if metric_name.lower() in tc.metric_name.lower():
                direction = "up" if tc.direction == "increasing" else "down"
                percentage = abs(tc.change_percentage)
                return (direction, f"{percentage:.0f}%")

        return None

    def _render_metric_cards(self, cards: List[Dict]) -> List[str]:
        """Render metric cards in a responsive grid layout.

        Args:
            cards: List of card data dictionaries

        Returns:
            List of markdown lines with HTML
        """
        lines = []
        lines.append('<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin-bottom: 24px;">')

        for card in cards:
            # Get trend indicator if available
            trend_html = ""
            if card["trend"]:
                direction, percentage = card["trend"]
                if direction == "up":
                    trend_color = COLOR_PALETTE["success"]
                    trend_icon = "↑"
                else:
                    trend_color = COLOR_PALETTE["danger"]
                    trend_icon = "↓"

                trend_html = f'<div style="color: {trend_color}; font-size: 14px; font-weight: 600; margin-top: 4px;">{trend_icon} {percentage}</div>'

            card_html = f'''
<div style="
    background: linear-gradient(135deg, {card["color"]}15 0%, {card["color"]}05 100%);
    border: 2px solid {card["color"]}40;
    border-radius: 12px;
    padding: 20px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    transition: all 0.3s ease;
">
    <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
        <span style="font-size: 32px;">{card["icon"]}</span>
        <div style="flex: 1;">
            <div style="color: #6b7280; font-size: 13px; font-weight: 500;">{card["title"]}</div>
            <div style="color: #111827; font-size: 28px; font-weight: 700; line-height: 1.2;">{card["value"]}</div>
        </div>
    </div>
    <div style="color: #6b7280; font-size: 13px; border-top: 1px solid {card["color"]}20; padding-top: 8px;">
        {card["subtitle"]}
        {trend_html}
    </div>
</div>
'''
            lines.append(card_html)

        lines.append('</div>')
        lines.append("")
        return lines
