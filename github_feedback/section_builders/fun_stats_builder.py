"""Fun statistics section builder for entertaining insights."""

from __future__ import annotations

from typing import List

from github_feedback.models import MetricSnapshot

from .base_builder import SectionBuilder


class FunStatsBuilder(SectionBuilder):
    """Builder for fun statistics section."""

    def build(self) -> List[str]:
        """Build the fun statistics section."""
        if not self.metrics.fun_statistics:
            return []

        fun_stats = self.metrics.fun_statistics
        lines = []

        lines.append("## 🎉 재미있는 통계")
        lines.append("")

        # Fun facts section
        if fun_stats.fun_facts:
            lines.append("### 🎯 재미있는 사실들")
            lines.append("")
            for fact in fun_stats.fun_facts:
                lines.append(f"- {fact}")
            lines.append("")

        # Work hours distribution
        if fun_stats.work_hours:
            lines.append("### ⏰ 작업 시간대 분석")
            lines.append("")
            lines.append(f"**활동 스타일:** {fun_stats.work_hours.work_style}")
            lines.append("")

            if fun_stats.work_hours.peak_hours:
                peak_hours_str = ", ".join(f"{h}시" for h in fun_stats.work_hours.peak_hours[:3])
                lines.append(f"**가장 활발한 시간대:** {peak_hours_str}")
                lines.append("")

            # Hour distribution chart
            lines.append(self._render_hour_chart(fun_stats.work_hours.hour_distribution))
            lines.append("")

        # Commit keywords word cloud
        if fun_stats.commit_keywords:
            lines.append("### 💬 커밋 메시지 키워드")
            lines.append("")
            lines.append(self._render_keyword_cloud(fun_stats.commit_keywords))
            lines.append("")

        # Top modified files
        if fun_stats.top_modified_files:
            lines.append("### 📁 자주 수정한 파일 TOP 10")
            lines.append("")
            lines.append("| 파일 | 수정 횟수 | 추가 | 삭제 |")
            lines.append("|------|-----------|------|------|")

            for file_activity in fun_stats.top_modified_files:
                filename = file_activity.filepath.split('/')[-1]  # Show just filename
                if len(filename) > 40:
                    filename = "..." + filename[-37:]

                lines.append(
                    f"| `{filename}` | {file_activity.modifications} | +{file_activity.lines_added} | -{file_activity.lines_deleted} |"
                )

            lines.append("")

        # PR size and weekend warrior
        lines.append("### 📊 활동 특징")
        lines.append("")

        if fun_stats.avg_pr_size:
            lines.append(f"**평균 PR 크기:** {fun_stats.avg_pr_size}")
            lines.append("")

        if fun_stats.weekend_warrior_score > 0:
            lines.append(f"**주말 활동 비율:** {fun_stats.weekend_warrior_score:.1f}%")
            if fun_stats.weekend_warrior_score >= 25:
                lines.append("🏖️ 주말에도 열심히 활동하는 주말 전사!")
            lines.append("")

        return lines

    def _render_hour_chart(self, hour_dist: dict) -> str:
        """Render hour distribution as a simple bar chart."""
        if not hour_dist:
            return ""

        max_count = max(hour_dist.values()) if hour_dist else 1
        lines = []

        lines.append('<div style="background: #f6f8fa; border-radius: 8px; padding: 16px;">')
        lines.append('<div style="font-size: 12px; color: #586069; margin-bottom: 12px;">시간대별 활동 분포</div>')

        # Create bars
        for hour in range(24):
            count = hour_dist.get(hour, 0)
            if count > 0:
                width_percent = (count / max_count) * 100
                lines.append(
                    f'<div style="display: flex; align-items: center; margin-bottom: 4px;">'
                    f'<div style="width: 40px; text-align: right; padding-right: 8px; font-size: 11px; color: #586069;">{hour:02d}시</div>'
                    f'<div style="flex: 1; background: #e1e4e8; border-radius: 3px; height: 20px; position: relative;">'
                    f'<div style="width: {width_percent}%; background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); height: 100%; border-radius: 3px;"></div>'
                    f'</div>'
                    f'<div style="width: 40px; padding-left: 8px; font-size: 11px; color: #586069;">{count}</div>'
                    f'</div>'
                )

        lines.append('</div>')

        return "\n".join(lines)

    def _render_keyword_cloud(self, keywords: dict) -> str:
        """Render keyword cloud with varying sizes."""
        if not keywords:
            return ""

        max_count = max(keywords.values()) if keywords else 1
        lines = []

        lines.append('<div style="background: #f6f8fa; border-radius: 8px; padding: 20px; display: flex; flex-wrap: wrap; gap: 12px; align-items: center; justify-content: center;">')

        for word, count in sorted(keywords.items(), key=lambda x: x[1], reverse=True):
            # Calculate font size based on frequency (12px to 32px)
            size = 12 + int((count / max_count) * 20)
            opacity = 0.6 + (count / max_count) * 0.4

            lines.append(
                f'<span style="font-size: {size}px; font-weight: 600; color: #667eea; opacity: {opacity};">{word}</span>'
            )

        lines.append('</div>')

        return "\n".join(lines)
