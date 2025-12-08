"""인터랙티브 컴포넌트 렌더링 메소드."""
from __future__ import annotations

from typing import Any, Dict, List

from ..constants import COLOR_PALETTE


class InteractiveRenderer:
    """인터랙티브 컴포넌트 렌더링 클래스."""

    @staticmethod
    def render_collapsible_section(
        section_id: str,
        title: str,
        content: List[str],
        collapsed: bool = False,
        icon: str = "📋"
    ) -> List[str]:
        """접을 수 있는 섹션 렌더링.

        Args:
            section_id: 고유 섹션 ID
            title: 섹션 제목
            content: 섹션 내용 (마크다운 라인 리스트)
            collapsed: 초기 접힌 상태 여부
            icon: 아이콘 이모지

        Returns:
            마크다운 라인 리스트
        """
        lines = []

        display_style = "none" if collapsed else "block"
        arrow_icon = "▶" if collapsed else "▼"

        lines.append(f'<div style="border: 2px solid {COLOR_PALETTE["gray_200"]}; border-radius: 12px; margin: 16px 0; background: white; box-shadow: 0 2px 4px rgba(0,0,0,0.1); overflow: hidden;">')

        # 헤더 (클릭 가능)
        lines.append(f'  <div onclick="toggleSection(\'{section_id}\')" style="padding: 16px 20px; background: linear-gradient(135deg, {COLOR_PALETTE["bg_gradient_purple_start"]} 0%, {COLOR_PALETTE["bg_gradient_purple_end"]} 100%); color: white; cursor: pointer; display: flex; justify-content: space-between; align-items: center; user-select: none; transition: opacity 0.2s;">')
        lines.append(f'    <div style="display: flex; align-items: center; gap: 12px;">')
        lines.append(f'      <span style="font-size: 1.5em;">{icon}</span>')
        lines.append(f'      <h3 style="margin: 0; font-size: 1.3em;">{title}</h3>')
        lines.append(f'    </div>')
        lines.append(f'    <span id="{section_id}-arrow" style="font-size: 1.2em; transition: transform 0.3s;">{arrow_icon}</span>')
        lines.append(f'  </div>')

        # 내용
        lines.append(f'  <div id="{section_id}-content" style="display: {display_style}; padding: 20px; animation: fadeIn 0.3s ease-out;">')
        lines.extend(content)
        lines.append(f'  </div>')

        lines.append('</div>')

        # JavaScript for toggle
        lines.append('<script>')
        lines.append('function toggleSection(sectionId) {')
        lines.append('  const content = document.getElementById(sectionId + "-content");')
        lines.append('  const arrow = document.getElementById(sectionId + "-arrow");')
        lines.append('  if (content.style.display === "none") {')
        lines.append('    content.style.display = "block";')
        lines.append('    arrow.textContent = "▼";')
        lines.append('  } else {')
        lines.append('    content.style.display = "none";')
        lines.append('    arrow.textContent = "▶";')
        lines.append('  }')
        lines.append('}')
        lines.append('</script>')
        lines.append("")

        return lines

    @staticmethod
    def render_filterable_list(
        items: List[Dict[str, Any]],
        title: str = "필터링 가능한 리스트",
        filter_key: str = "category",
        display_key: str = "name",
        description_key: str = "description"
    ) -> List[str]:
        """필터링 가능한 리스트 렌더링.

        Args:
            items: 아이템 리스트 [{"category": "언어", "name": "Python", "description": "..."}, ...]
            title: 리스트 제목
            filter_key: 필터링할 키
            display_key: 표시할 이름 키
            description_key: 설명 키

        Returns:
            마크다운 라인 리스트
        """
        if not items:
            return []

        lines = []

        # 카테고리 추출
        categories = list(set(item.get(filter_key, "기타") for item in items))
        categories.sort()

        lines.append(f'<div style="border: 2px solid {COLOR_PALETTE["gray_200"]}; border-radius: 12px; padding: 24px; margin: 16px 0; background: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">')
        lines.append(f'  <h4 style="margin: 0 0 20px 0; color: {COLOR_PALETTE["gray_800"]}; font-size: 1.3em;">{title}</h4>')

        # 필터 버튼
        lines.append('  <div style="display: flex; gap: 8px; margin-bottom: 20px; flex-wrap: wrap;">')
        lines.append(f'    <button onclick="filterItems(\'all\')" class="filter-btn active" data-filter="all" style="padding: 8px 16px; border: 2px solid {COLOR_PALETTE["primary"]}; background: {COLOR_PALETTE["primary"]}; color: white; border-radius: 8px; cursor: pointer; font-weight: bold; transition: all 0.3s;">전체</button>')

        for cat in categories:
            lines.append(f'    <button onclick="filterItems(\'{cat}\')" class="filter-btn" data-filter="{cat}" style="padding: 8px 16px; border: 2px solid {COLOR_PALETTE["gray_300"]}; background: white; color: {COLOR_PALETTE["gray_700"]}; border-radius: 8px; cursor: pointer; font-weight: 500; transition: all 0.3s;">{cat}</button>')

        lines.append('  </div>')

        # 아이템 리스트
        lines.append('  <div id="items-container">')

        for idx, item in enumerate(items):
            cat = item.get(filter_key, "기타")
            name = item.get(display_key, "")
            desc = item.get(description_key, "")

            lines.append(f'    <div class="list-item" data-category="{cat}" style="padding: 16px; margin-bottom: 12px; background: {COLOR_PALETTE["gray_50"]}; border-radius: 8px; border-left: 4px solid {COLOR_PALETTE["primary"]}; transition: all 0.3s;">')
            lines.append(f'      <div style="font-weight: bold; color: {COLOR_PALETTE["gray_800"]}; margin-bottom: 4px;">{name}</div>')
            lines.append(f'      <div style="color: {COLOR_PALETTE["gray_600"]}; font-size: 0.9em;">{desc}</div>')
            lines.append(f'      <div style="margin-top: 8px; color: {COLOR_PALETTE["gray_500"]}; font-size: 0.85em;">카테고리: {cat}</div>')
            lines.append('    </div>')

        lines.append('  </div>')
        lines.append('</div>')

        # JavaScript for filtering
        lines.append('<script>')
        lines.append('function filterItems(category) {')
        lines.append('  const items = document.querySelectorAll(".list-item");')
        lines.append('  const buttons = document.querySelectorAll(".filter-btn");')
        lines.append('  ')
        lines.append('  // Update button styles')
        lines.append('  buttons.forEach(btn => {')
        lines.append('    if (btn.dataset.filter === category) {')
        lines.append(f'      btn.style.background = "{COLOR_PALETTE["primary"]}";')
        lines.append('      btn.style.color = "white";')
        lines.append(f'      btn.style.borderColor = "{COLOR_PALETTE["primary"]}";')
        lines.append('    } else {')
        lines.append('      btn.style.background = "white";')
        lines.append(f'      btn.style.color = "{COLOR_PALETTE["gray_700"]}";')
        lines.append(f'      btn.style.borderColor = "{COLOR_PALETTE["gray_300"]}";')
        lines.append('    }')
        lines.append('  });')
        lines.append('  ')
        lines.append('  // Filter items')
        lines.append('  items.forEach(item => {')
        lines.append('    if (category === "all" || item.dataset.category === category) {')
        lines.append('      item.style.display = "block";')
        lines.append('    } else {')
        lines.append('      item.style.display = "none";')
        lines.append('    }')
        lines.append('  });')
        lines.append('}')
        lines.append('</script>')
        lines.append("")

        return lines


__all__ = ["InteractiveRenderer"]
