"""기술 스택 분석 섹션 - RPG 장비 시스템으로 시각화."""

from __future__ import annotations

from collections import defaultdict
from typing import Dict, List

from ..tech_stack_config import (
    EQUIPMENT_SLOTS,
    TECH_CATEGORIES,
    TECH_CUSTOM_ICONS,
    WEAPON_TIERS,
)
from ...game_elements import GameRenderer


def generate_tech_stack_analysis(tech_stack: List[tuple]) -> List[str]:
    """무기 장비 분석 생성 - 7단계 등급 시스템 및 장비 슬롯 시스템."""
    lines = [
        "## ⚔️ 장착 무기 및 장비 (기술 스택)",
        "",
        "> 한 해 동안 사용한 언어와 프레임워크를 RPG 장비 시스템으로 시각화",
        "",
    ]

    if not tech_stack:
        lines.append("_기술 데이터가 없습니다._")
        lines.extend(["", "---", ""])
        return lines

    total_changes = sum(count for _, count in tech_stack)

    # Categorize technologies
    categorized_tech = _categorize_technologies(tech_stack, total_changes)

    # Determine equipped items
    equipped_tech_names = _determine_equipped_items(categorized_tech)

    # Render inventory tables
    lines.extend(_render_inventory_section(categorized_tech, equipped_tech_names))

    # Render diversity analysis
    lines.extend(_render_diversity_analysis(tech_stack, categorized_tech))

    lines.extend(["---", ""])
    return lines


def _categorize_technologies(
    tech_stack: List[tuple], total_changes: int
) -> Dict[str, List[Dict]]:
    """Categorize technologies by type with metadata."""
    categorized_tech = {
        "language": [],
        "framework": [],
        "tool": [],
        "unknown": []
    }

    for lang, count in tech_stack:
        percentage = (count / total_changes * 100) if total_changes > 0 else 0
        category = TECH_CATEGORIES.get(lang, "unknown")

        # Determine weapon tier
        tier_info = None
        for tier in WEAPON_TIERS:
            if percentage >= tier["threshold"]:
                tier_info = tier
                break

        # Get custom icons and weapon info
        custom = TECH_CUSTOM_ICONS.get(lang, {})
        icon = custom.get("icon", "🔹")
        weapon_name = custom.get("weapon_name", lang)
        weapon_traits = custom.get("weapon_traits", [])

        tech_info = {
            "name": lang,
            "count": count,
            "percentage": percentage,
            "tier": tier_info,
            "icon": icon,
            "weapon_name": weapon_name,
            "weapon_traits": weapon_traits
        }

        categorized_tech[category].append(tech_info)

    return categorized_tech


def _determine_equipped_items(categorized_tech: Dict[str, List[Dict]]) -> set:
    """Determine which items are currently equipped (top items per category)."""
    equipped_tech_names = set()

    # Main weapon slot (languages, max 3)
    for tech in categorized_tech["language"][:3]:
        equipped_tech_names.add(tech["name"])

    # Secondary weapon slot (frameworks, max 3)
    for tech in categorized_tech["framework"][:3]:
        equipped_tech_names.add(tech["name"])

    # Accessory slot (tools, max 4)
    for tech in categorized_tech["tool"][:4]:
        equipped_tech_names.add(tech["name"])

    return equipped_tech_names


def _render_inventory_section(
    categorized_tech: Dict[str, List[Dict]], equipped_tech_names: set
) -> List[str]:
    """Render complete inventory with categorized tables."""
    lines = [
        "### 📊 장비 및 인벤토리",
        "",
        "> 한 해 동안 사용한 모든 기술의 상세 통계 (⭐ 표시는 현재 장착 중인 장비)",
        "",
    ]

    # Category display configuration
    categories_to_display = [
        ("language", "🎯 주무기 (프로그래밍 언어)", categorized_tech["language"]),
        ("framework", "🛡️ 보조무기 (프레임워크 & 라이브러리)", categorized_tech["framework"]),
        ("tool", "💍 장신구 (도구, DB, 인프라)", categorized_tech["tool"]),
    ]

    for category_key, category_title, tech_list in categories_to_display:
        if not tech_list:
            continue

        lines.append(f"#### {category_title}")
        lines.append("")

        # Build table
        headers = ["순위", "상태", "아이콘", "장비명 & 특성", "등급", "사용 횟수", "비율", "강화도"]
        rows = []

        for idx, tech in enumerate(tech_list[:15], 1):
            rows.append(_build_tech_row(idx, tech, equipped_tech_names))

        # Render HTML table
        lines.extend(GameRenderer.render_html_table(
            headers=headers,
            rows=rows,
            title="",
            description="",
            striped=True,
            escape_cells=False
        ))
        lines.append("")

    # Unknown category
    if categorized_tech["unknown"]:
        lines.extend(_render_unknown_category(categorized_tech["unknown"], equipped_tech_names))

    return lines


def _build_tech_row(idx: int, tech: Dict, equipped_tech_names: set) -> List[str]:
    """Build a single technology row for the table."""
    tier = tech["tier"]
    percentage = tech["percentage"]

    # Equipped badge
    if tech["name"] in equipped_tech_names:
        equipped_badge = '<span style="background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%); color: white; padding: 4px 10px; border-radius: 12px; font-size: 0.85em; font-weight: bold; white-space: nowrap; box-shadow: 0 2px 8px rgba(251, 191, 36, 0.5), 0 0 20px rgba(251, 191, 36, 0.3); animation: glow 2s ease-in-out infinite;">⭐ 장착 중</span>'
    else:
        equipped_badge = '<span style="color: #9ca3af; font-size: 0.85em;">-</span>'

    # Progress bar
    progress_bar = f'<div style="background: #e5e7eb; border-radius: 6px; height: 22px; width: 100%; max-width: 200px; overflow: hidden; box-shadow: inset 0 1px 3px rgba(0,0,0,0.1);"><div style="background: {tier["color"]}; height: 100%; width: {percentage}%; border-radius: 6px; box-shadow: 0 0 15px {tier["glow"]}; transition: width 0.8s cubic-bezier(0.4, 0, 0.2, 1); position: relative; overflow: hidden;"><div style="position: absolute; top: 0; left: 0; right: 0; bottom: 0; background: linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.3) 50%, transparent 100%); animation: shimmer 2s infinite;"></div></div></div>'

    # Tier badge
    glow_intensity = "0 0 10px" if tier["name"] in ["신화", "전설"] else "0 0 5px"
    tier_badge = f'<span style="background: {tier["color"]}; color: white; padding: 4px 10px; border-radius: 12px; font-size: 0.85em; font-weight: bold; white-space: nowrap; box-shadow: {glow_intensity} {tier["glow"]};">{tier["prefix"]} {tier["name"]}</span>'

    # Weapon name cell
    weapon_name_cell = f'<strong>{tech["weapon_name"]}</strong><br><span style="color: #6b7280; font-size: 0.9em;">({tech["name"]})</span>'
    if tech.get("weapon_traits"):
        weapon_name_cell += '<div style="margin-top: 8px; padding: 8px; background: #f9fafb; border-left: 3px solid ' + tier["color"] + '; border-radius: 4px;">'
        for trait in tech["weapon_traits"]:
            weapon_name_cell += f'<div style="font-size: 0.85em; color: #4b5563; margin-bottom: 3px; line-height: 1.4;">• {trait}</div>'
        weapon_name_cell += '</div>'

    return [
        f"#{idx}",
        equipped_badge,
        f'<span style="font-size: 1.5em;">{tech["icon"]}</span>',
        weapon_name_cell,
        tier_badge,
        f'{tech["count"]:,}회',
        f'<strong style="color: {tier["color"]};">{percentage:.1f}%</strong>',
        progress_bar
    ]


def _render_unknown_category(unknown_tech: List[Dict], equipped_tech_names: set) -> List[str]:
    """Render unknown/miscellaneous technologies."""
    lines = [
        "#### 🔹 기타 기술",
        "",
    ]

    headers = ["순위", "상태", "기술명", "등급", "사용 횟수", "비율", "강화도"]
    rows = []

    for idx, tech in enumerate(unknown_tech[:10], 1):
        tier = tech["tier"]
        percentage = tech["percentage"]

        # Equipped badge
        if tech["name"] in equipped_tech_names:
            equipped_badge = '<span style="background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%); color: white; padding: 4px 10px; border-radius: 12px; font-size: 0.85em; font-weight: bold; white-space: nowrap; box-shadow: 0 2px 8px rgba(251, 191, 36, 0.5), 0 0 20px rgba(251, 191, 36, 0.3); animation: glow 2s ease-in-out infinite;">⭐ 장착 중</span>'
        else:
            equipped_badge = '<span style="color: #9ca3af; font-size: 0.85em;">-</span>'

        progress_bar = f'<div style="background: #e5e7eb; border-radius: 4px; height: 20px; width: 100%; max-width: 200px;"><div style="background: {tier["color"]}; height: 100%; width: {percentage}%; border-radius: 4px;"></div></div>'
        tier_badge = f'<span style="background: {tier["color"]}; color: white; padding: 4px 10px; border-radius: 12px; font-size: 0.85em; font-weight: bold;">{tier["prefix"]} {tier["name"]}</span>'

        rows.append([
            f"#{idx}",
            equipped_badge,
            f"**{tech['name']}**",
            tier_badge,
            f'{tech["count"]:,}회',
            f'{percentage:.1f}%',
            progress_bar
        ])

    lines.extend(GameRenderer.render_html_table(
        headers=headers,
        rows=rows,
        title="",
        description="",
        striped=True,
        escape_cells=False
    ))
    lines.append("")

    return lines


def _render_diversity_analysis(
    tech_stack: List[tuple], categorized_tech: Dict[str, List[Dict]]
) -> List[str]:
    """Render technology diversity analysis."""
    lines = [
        "### 📈 기술 스택 다양성 분석",
        "",
    ]

    diversity_stats = f"""
**📊 기술 통계**
- 🎯 주무기 (언어): {len(categorized_tech["language"])}개
- 🛡️ 보조무기 (프레임워크): {len(categorized_tech["framework"])}개
- 💍 장신구 (도구): {len(categorized_tech["tool"])}개
- 🔹 기타: {len(categorized_tech["unknown"])}개
- ⚡ **총 기술 스택**: {len(tech_stack)}개

**🏆 다양성 평가**
"""

    tech_count = len(tech_stack)
    if tech_count >= 20:
        diversity_stats += "- 💎 **전설급 다재다능**: 매우 다양한 기술 스택을 활용하고 있습니다!"
    elif tech_count >= 15:
        diversity_stats += "- ⚔️ **마스터 레벨**: 폭넓은 기술 스택을 보유하고 있습니다!"
    elif tech_count >= 10:
        diversity_stats += "- 🗡️ **숙련자 레벨**: 균형잡힌 기술 스택을 가지고 있습니다."
    elif tech_count >= 5:
        diversity_stats += "- 🔪 **성장 중**: 핵심 기술에 집중하고 있습니다."
    else:
        diversity_stats += "- 🔧 **전문가 지향**: 특정 기술에 깊이 있게 집중하고 있습니다."

    lines.extend(GameRenderer.render_info_box(
        title="🎯 기술 스택 종합 평가",
        content=diversity_stats.strip(),
        emoji="📊",
        bg_color="#f0f9ff",
        border_color="#3b82f6"
    ))

    return lines


__all__ = ["generate_tech_stack_analysis"]
