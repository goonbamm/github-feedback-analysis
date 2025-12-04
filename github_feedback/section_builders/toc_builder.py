"""Table of Contents navigation builder."""

from typing import List, Tuple

from ..game_elements import COLOR_PALETTE
from ..models import MetricSnapshot
from .base_builder import SectionBuilder


class TOCBuilder(SectionBuilder):
    """Builder for Table of Contents navigation."""

    def build(self) -> List[str]:
        """Build TOC navigation section.

        Returns:
            List of markdown lines for TOC section
        """
        lines = []

        # Get all sections that will be present in the report
        sections = self._get_available_sections()

        if not sections:
            return lines

        # Build sticky navigation with HTML
        lines.append(self._render_toc_navigation(sections))
        lines.append("")
        return lines

    def _get_available_sections(self) -> List[Tuple[str, str, str]]:
        """Get list of available sections based on metrics data.

        Returns:
            List of tuples (section_name, section_emoji, section_anchor)
        """
        sections = []

        # Always present sections
        sections.append(("한눈에 보는 요약", "📊", "한눈에-보는-요약"))
        sections.append(("핵심 지표 대시보드", "📊", "핵심-지표-대시보드"))
        sections.append(("저장소 캐릭터 스탯", "🎮", "저장소-캐릭터-스탯"))

        # Conditional sections
        if self.metrics.skill_tree:
            sections.append(("스킬 트리", "🌳", "스킬-트리"))

        if self.metrics.awards:
            sections.append(("Awards Cabinet", "🏆", "awards-cabinet"))

        if self.metrics.highlights:
            sections.append(("Growth Highlights", "✨", "growth-highlights"))

        if self.metrics.monthly_trends:
            sections.append(("Monthly Trends", "📈", "monthly-trends"))

        if self.metrics.detailed_feedback:
            sections.append(("Detailed Feedback", "📋", "detailed-feedback"))

        if self.metrics.retrospective:
            sections.append(("Deep Retrospective", "🔍", "deep-retrospective"))

        if hasattr(self.metrics, 'witch_critique') and self.metrics.witch_critique:
            sections.append(("마녀의 신랄한 평가", "🧙‍♀️", "마녀의-신랄한-평가"))

        if self.metrics.spotlight_examples:
            sections.append(("Spotlight Examples", "🌟", "spotlight-examples"))

        if self.metrics.tech_stack:
            sections.append(("Tech Stack", "💻", "tech-stack"))

        return sections

    def _render_toc_navigation(self, sections: List[Tuple[str, str, str]]) -> str:
        """Render TOC navigation with HTML.

        Args:
            sections: List of (name, emoji, anchor) tuples

        Returns:
            HTML string for TOC navigation
        """
        # Create navigation items
        nav_items = []
        for name, emoji, anchor in sections:
            nav_items.append(
                f'<a href="#{anchor}" style="color: {COLOR_PALETTE["gray_700"]}; text-decoration: none; padding: 8px 12px; border-radius: 6px; transition: all 0.2s; display: block;">'
                f'{emoji} {name}'
                f'</a>'
            )

        nav_items_html = "\n".join(nav_items)

        toc_html = f'''
<div style="
    background: linear-gradient(135deg, {COLOR_PALETTE["bg_gradient_purple_start"]}15 0%, {COLOR_PALETTE["bg_gradient_purple_end"]}15 100%);
    border: 2px solid {COLOR_PALETTE["primary"]}30;
    border-radius: 16px;
    padding: 24px;
    margin-bottom: 32px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.08);
">
    <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 16px;">
        <span style="font-size: 24px;">📑</span>
        <h3 style="margin: 0; font-size: 20px; font-weight: 700; color: {COLOR_PALETTE["gray_900"]};">목차 (Table of Contents)</h3>
    </div>
    <div style="
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 8px;
    ">
        {nav_items_html}
    </div>
</div>

<style>
div[style*="display: grid"] a:hover {{
    background-color: {COLOR_PALETTE["primary"]}20;
    transform: translateX(4px);
}}
</style>
'''

        return toc_html
