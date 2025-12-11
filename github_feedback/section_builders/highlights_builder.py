"""Highlights section builder."""

from typing import List

from ..game_elements import GameRenderer
from ..core.models import MetricSnapshot
from .base_builder import SectionBuilder


class HighlightsBuilder(SectionBuilder):
    """Builder for growth highlights section."""

    def build(self) -> List[str]:
        """Build growth highlights section.

        Returns:
            List of markdown lines for highlights section
        """
        if not self.metrics.highlights:
            return []

        lines = ["## ✨ Growth Highlights", ""]
        lines.append("> 이번 기간 동안의 주요 성과와 성장 포인트")
        lines.append("")

        # Build HTML table
        headers = ["#", "성과"]
        rows = [[str(i), highlight] for i, highlight in enumerate(self.metrics.highlights, 1)]

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
