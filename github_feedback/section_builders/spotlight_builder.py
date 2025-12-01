"""Spotlight examples section builder."""

from typing import List

from ..game_elements import GameRenderer
from ..models import MetricSnapshot
from .base_builder import SectionBuilder


class SpotlightBuilder(SectionBuilder):
    """Builder for spotlight examples section."""

    def build(self) -> List[str]:
        """Build spotlight examples section.

        Returns:
            List of markdown lines for spotlight section
        """
        if not self.metrics.spotlight_examples:
            return []

        # Filter out categories with no entries
        non_empty_categories = {
            category: entries
            for category, entries in self.metrics.spotlight_examples.items()
            if entries
        }

        # If no categories have content, don't create the section
        if not non_empty_categories:
            return []

        lines = ["## 🎯 Spotlight Examples", ""]
        lines.append("> 주목할 만한 기여 사례")
        lines.append("")

        for category, entries in non_empty_categories.items():
            lines.append(f"### {category.replace('_', ' ').title()}")
            lines.append("")

            # Build table data
            headers = ["사례"]
            rows = [[entry] for entry in entries]

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
