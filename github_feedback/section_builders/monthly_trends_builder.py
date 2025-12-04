"""Monthly trends section builder."""

from typing import List

from ..game_elements import GameRenderer
from ..models import MetricSnapshot
from .base_builder import SectionBuilder


class MonthlyTrendsBuilder(SectionBuilder):
    """Builder for monthly trends section."""

    def build(self) -> List[str]:
        """Build monthly trends section with charts and insights.

        Returns:
            List of markdown lines for monthly trends section
        """
        if not self.metrics.monthly_trends:
            return []

        lines = ["## 📈 Monthly Trends", ""]
        lines.append("> 월별 활동 패턴과 트렌드 분석")
        lines.append("")

        # Insights as info box
        if self.metrics.monthly_insights and self.metrics.monthly_insights.insights:
            insights_text = "\n".join(f"{i}. {insight}" for i, insight in enumerate(self.metrics.monthly_insights.insights, 1))
            lines.extend(GameRenderer.render_info_box(
                title="주요 인사이트",
                content=insights_text,
                emoji="💡",
                bg_color="#fffbeb",
                border_color="#f59e0b"
            ))

        # Render line chart for trends
        lines.append("### 📈 월별 활동 추세")
        lines.append("")

        # Prepare data for line chart
        months_labels = [trend.month for trend in self.metrics.monthly_trends]

        # Create datasets for multi-line chart
        datasets = [
            {
                "label": "커밋",
                "data": [trend.commits for trend in self.metrics.monthly_trends],
                "color": "#3b82f6"
            },
            {
                "label": "PR",
                "data": [trend.pull_requests for trend in self.metrics.monthly_trends],
                "color": "#8b5cf6"
            },
            {
                "label": "리뷰",
                "data": [trend.reviews for trend in self.metrics.monthly_trends],
                "color": "#10b981"
            },
            {
                "label": "이슈",
                "data": [trend.issues for trend in self.metrics.monthly_trends],
                "color": "#f59e0b"
            }
        ]

        lines.extend(GameRenderer.render_line_chart(
            labels=months_labels,
            datasets=datasets,
            title="월별 활동 추세",
            x_label="월",
            y_label="활동 수"
        ))

        # Render detailed data table with visual bars
        lines.append("### 📊 월별 활동 데이터")
        lines.append("")

        # Calculate max activity for visual bars
        max_activity = 0
        for trend in self.metrics.monthly_trends:
            total_activity = trend.commits + trend.pull_requests + trend.reviews + trend.issues
            if total_activity > max_activity:
                max_activity = total_activity

        headers = ["월", "커밋", "PR", "리뷰", "이슈", "총 활동", "활동량 시각화"]
        rows = []
        for trend in self.metrics.monthly_trends:
            total_activity = trend.commits + trend.pull_requests + trend.reviews + trend.issues

            # Create visual bar for total activity
            bar_percentage = int((total_activity / max_activity * 100)) if max_activity > 0 else 0
            visual_bar = f'<div style="background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); height: 20px; width: {bar_percentage}%; border-radius: 4px; min-width: 2px;"></div>'

            rows.append([
                trend.month,
                str(trend.commits),
                str(trend.pull_requests),
                str(trend.reviews),
                str(trend.issues),
                f"<strong>{total_activity}</strong>",
                visual_bar
            ])

        lines.extend(GameRenderer.render_html_table(
            headers=headers,
            rows=rows,
            title="",
            description="",
            striped=True,
            escape_cells=False
        ))

        lines.append("---")
        lines.append("")
        return lines
