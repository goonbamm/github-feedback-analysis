"""Awards section builder."""

from typing import List

from ..core.constants import AWARD_CATEGORIES, AWARD_KEYWORDS
from ..game_elements import GameRenderer
from ..core.models import MetricSnapshot
from .base_builder import SectionBuilder


class AwardsBuilder(SectionBuilder):
    """Builder for awards cabinet section."""

    def build(self) -> List[str]:
        """Build awards cabinet section.

        Returns:
            List of markdown lines for awards section
        """
        if not self.metrics.awards:
            return []

        lines = ["## 🏆 Awards Cabinet", ""]
        lines.append(f"**총 {len(self.metrics.awards)}개의 어워드를 획득했습니다!**")
        lines.append("")

        categories = self._categorize_awards(self.metrics.awards)

        # Build awards grid with HTML
        awards_data = []
        for category_name, category_awards in categories.items():
            if category_awards:
                # Extract emoji from category name
                emoji = category_name.split()[0] if category_name else "🏆"
                category_title = " ".join(category_name.split()[1:]) if len(category_name.split()) > 1 else category_name

                # Combine all awards in this category
                description = "<br>".join(f"• {award}" for award in category_awards)

                awards_data.append({
                    "category": category_title,
                    "description": description,
                    "emoji": emoji,
                    "count": str(len(category_awards))
                })

        # Render using HTML
        lines.extend(GameRenderer.render_awards_grid(awards_data, columns=2))

        lines.append("---")
        lines.append("")
        return lines

    def _categorize_awards(self, awards: List[str]) -> dict:
        """Categorize awards by type for better organization.

        Args:
            awards: List of award strings

        Returns:
            Dictionary mapping category labels to list of awards
        """
        # Initialize categories from constants
        categories = {label: [] for label in AWARD_CATEGORIES.values()}

        for award in awards:
            categorized = False
            # Check each category's keywords
            for category_key, keywords in AWARD_KEYWORDS.items():
                if any(keyword in award for keyword in keywords):
                    category_label = AWARD_CATEGORIES[category_key]
                    categories[category_label].append(award)
                    categorized = True
                    break

            # Default category if no keywords match
            if not categorized:
                categories[AWARD_CATEGORIES['basic']].append(award)

        # Remove empty categories
        return {k: v for k, v in categories.items() if v}
