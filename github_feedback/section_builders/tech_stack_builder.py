"""Tech stack section builder."""

from typing import List

from ..constants import DISPLAY_LIMITS
from ..game_elements import GameRenderer
from ..models import MetricSnapshot
from .base_builder import SectionBuilder


class TechStackBuilder(SectionBuilder):
    """Builder for tech stack analysis section."""

    def build(self) -> List[str]:
        """Build tech stack analysis section.

        Returns:
            List of markdown lines for tech stack section
        """
        if not self.metrics.tech_stack:
            return []

        # Check if there are any languages to display
        if not self.metrics.tech_stack.top_languages:
            return []

        lines = ["## 💻 Tech Stack Analysis", ""]
        lines.append("> 사용한 기술과 언어 분포")
        lines.append("")
        lines.append(f"**다양성 점수**: {self.metrics.tech_stack.diversity_score:.2f} (0-1 척도)")
        lines.append("")

        # Build table data
        headers = ["순위", "언어", "파일 수"]
        rows = []
        for i, lang in enumerate(self.metrics.tech_stack.top_languages[:DISPLAY_LIMITS['top_languages']], 1):
            count = self.metrics.tech_stack.languages.get(lang, 0)
            rows.append([str(i), lang, f"{count:,}"])

        # Render as HTML table
        lines.extend(GameRenderer.render_html_table(
            headers=headers,
            rows=rows,
            title="",
            description="",
            striped=True
        ))

        lines.append("---")
        lines.append("")
        return lines
