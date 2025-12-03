"""게임 요소 렌더링 및 계산 유틸리티.

이 모듈은 모든 보고서에서 사용하는 공통 게임 요소를 제공합니다:
- RPG 스타일 캐릭터 스탯 박스
- 스킬 카드 시스템
- 레벨 및 타이틀 계산
"""
from __future__ import annotations

from typing import Any, Dict, List, Tuple

import html

from .utils import pad_to_width


# ============================================
# 🎨 중앙 색상 팔레트 시스템
# ============================================
COLOR_PALETTE = {
    # Primary Colors
    "primary": "#667eea",
    "primary_dark": "#5568d3",
    "primary_light": "#818cf8",
    "secondary": "#764ba2",
    "secondary_dark": "#6b4193",
    "secondary_light": "#8b5cf6",

    # Status Colors
    "success": "#10b981",
    "success_dark": "#059669",
    "success_light": "#34d399",
    "warning": "#f59e0b",
    "warning_dark": "#d97706",
    "warning_light": "#fbbf24",
    "danger": "#ef4444",
    "danger_dark": "#dc2626",
    "danger_light": "#f87171",
    "info": "#3b82f6",
    "info_dark": "#2563eb",
    "info_light": "#60a5fa",

    # Neutral Colors
    "gray_50": "#f9fafb",
    "gray_100": "#f3f4f6",
    "gray_200": "#e5e7eb",
    "gray_300": "#d1d5db",
    "gray_400": "#9ca3af",
    "gray_500": "#6b7280",
    "gray_600": "#4b5563",
    "gray_700": "#374151",
    "gray_800": "#1f2937",
    "gray_900": "#111827",

    # Special Colors
    "gold": "#fbbf24",
    "gold_dark": "#f59e0b",
    "gold_light": "#fcd34d",
    "pink": "#ec4899",
    "pink_dark": "#db2777",
    "pink_light": "#f472b6",
    "purple": "#8b5cf6",
    "purple_dark": "#7c3aed",
    "purple_light": "#a78bfa",
    "orange": "#f97316",
    "orange_dark": "#ea580c",
    "orange_light": "#fb923c",

    # RPG Stat Colors
    "stat_code_quality": "#3b82f6",
    "stat_collaboration": "#8b5cf6",
    "stat_problem_solving": "#ec4899",
    "stat_productivity": "#f59e0b",
    "stat_consistency": "#f97316",
    "stat_growth": "#10b981",

    # Background Colors
    "bg_gradient_purple_start": "#667eea",
    "bg_gradient_purple_end": "#764ba2",
    "bg_gradient_gold_start": "#fef3c7",
    "bg_gradient_gold_end": "#fde68a",
    "bg_gradient_dark_start": "#1a202c",
    "bg_gradient_dark_end": "#2d3748",
}


# ============================================
# 🎨 CSS 애니메이션 및 스타일 헬퍼
# ============================================
def get_animation_styles() -> str:
    """Return CSS animation styles for enhanced UI."""
    return """
<style>
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}

@keyframes slideIn {
    from { transform: translateX(-20px); opacity: 0; }
    to { transform: translateX(0); opacity: 1; }
}

@keyframes fillBar {
    from { width: 0%; }
    to { width: var(--target-width); }
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.7; }
}

@keyframes glow {
    0%, 100% { box-shadow: 0 0 5px rgba(102, 126, 234, 0.5); }
    50% { box-shadow: 0 0 20px rgba(102, 126, 234, 0.8), 0 0 30px rgba(118, 75, 162, 0.6); }
}

@keyframes shimmer {
    0% { background-position: -1000px 0; }
    100% { background-position: 1000px 0; }
}

.animate-fade-in {
    animation: fadeIn 0.6s ease-out;
}

.animate-slide-in {
    animation: slideIn 0.6s ease-out;
}

.animate-pulse {
    animation: pulse 2s ease-in-out infinite;
}

.animate-glow {
    animation: glow 2s ease-in-out infinite;
}

/* Hover effects */
.hover-lift {
    transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.hover-lift:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 16px rgba(0, 0, 0, 0.2) !important;
}

/* Loading skeleton */
.skeleton {
    background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
    background-size: 200% 100%;
    animation: shimmer 1.5s infinite;
}
</style>
"""


class GameRenderer:
    """게임 스타일 시각화 렌더러."""

    @staticmethod
    def _wrap_text(text: str, max_width: int) -> List[str]:
        """텍스트를 최대 너비로 나누어 여러 줄로 반환.

        Args:
            text: 나눌 텍스트
            max_width: 한 줄의 최대 디스플레이 너비

        Returns:
            나누어진 텍스트 줄 리스트
        """
        from .utils import display_width

        if display_width(text) <= max_width:
            return [text]

        lines = []
        current_line = ""
        words = text.split()

        for word in words:
            test_line = f"{current_line} {word}".strip()
            if display_width(test_line) <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word

        if current_line:
            lines.append(current_line)

        return lines if lines else [text[:max_width]]

    @staticmethod
    def render_skill_card(
        skill_name: str,
        skill_type: str,
        mastery_level: int,
        effect_description: str,
        evidence: List[str],
        skill_emoji: str = "💎"
    ) -> List[str]:
        """게임 스타일 스킬 카드 렌더링 (HTML 테이블 사용).

        Args:
            skill_name: 스킬 이름
            skill_type: 타입 (패시브/액티브/성장중/미습득)
            mastery_level: 마스터리 퍼센트 (0-100)
            effect_description: 스킬 효과 설명
            evidence: 증거/습득 경로 리스트
            skill_emoji: 스킬 이모지

        Returns:
            마크다운 라인 리스트
        """
        lines = []

        # 마스터리에서 레벨 계산 (0-5 별)
        stars = min(5, mastery_level // 20)
        star_display = "★" * stars + "☆" * (5 - stars)
        level = min(5, (mastery_level // 20) + 1)

        # 타입 이모지 매핑
        type_emojis = {
            "패시브": "🟢",
            "액티브": "🔵",
            "성장중": "🟡",
            "미습득": "🔴"
        }
        type_emoji = type_emojis.get(skill_type, "⚪")

        # 마스터리 바 (진행률을 시각적으로 표현)
        mastery_percentage = mastery_level
        bar_filled_width = mastery_percentage  # CSS에서 퍼센트로 사용

        # HTML 테이블로 스킬 카드 렌더링
        lines.append('<div style="border: 2px solid #444; border-radius: 8px; padding: 16px; margin: 16px 0; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; font-family: \'Segoe UI\', Tahoma, Geneva, Verdana, sans-serif;">')

        # 스킬명 및 레벨
        lines.append(f'  <div style="font-size: 1.3em; font-weight: bold; margin-bottom: 8px; word-wrap: break-word; overflow-wrap: break-word; line-height: 1.4;">')
        lines.append(f'    {skill_emoji} {skill_name} <span style="background: rgba(255,255,255,0.2); padding: 2px 8px; border-radius: 4px; font-size: 0.8em;">Lv.{level}</span>')
        lines.append(f'  </div>')

        # 별 표시
        lines.append(f'  <div style="margin-bottom: 12px; font-size: 1.2em; color: #ffd700;">')
        lines.append(f'    {star_display}')
        lines.append(f'  </div>')

        # 스킬 타입
        lines.append(f'  <table style="width: 100%; border-collapse: collapse; margin-bottom: 8px;">')
        lines.append(f'    <tr>')
        lines.append(f'      <td style="padding: 8px; background: rgba(0,0,0,0.2); border-radius: 4px;"><strong>타입</strong></td>')
        lines.append(f'      <td style="padding: 8px; background: rgba(0,0,0,0.2); border-radius: 4px;">{type_emoji} {skill_type}</td>')
        lines.append(f'    </tr>')
        lines.append(f'  </table>')

        # 효과 설명
        lines.append(f'  <div style="background: rgba(0,0,0,0.2); padding: 12px; border-radius: 4px; margin-bottom: 12px;">')
        lines.append(f'    <div style="font-weight: bold; margin-bottom: 4px;">💫 효과</div>')
        lines.append(f'    <div style="opacity: 0.95; word-wrap: break-word; overflow-wrap: break-word; white-space: pre-wrap; line-height: 1.6;">{effect_description}</div>')
        lines.append(f'  </div>')

        # 마스터리 바 (개선된 버전 with 애니메이션)
        lines.append(f'  <div style="margin-bottom: 12px;">')
        lines.append(f'    <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">')
        lines.append(f'      <span style="font-weight: bold; font-size: 0.95em;">마스터리</span>')
        lines.append(f'      <span style="font-weight: bold; color: {COLOR_PALETTE["success_light"]}; font-size: 0.95em;">{mastery_percentage}%</span>')
        lines.append(f'    </div>')
        lines.append(f'    <div style="background: rgba(0,0,0,0.3); border-radius: 12px; height: 24px; overflow: hidden; position: relative; box-shadow: inset 0 2px 4px rgba(0,0,0,0.2);">')
        lines.append(f'      <div style="background: linear-gradient(90deg, {COLOR_PALETTE["success"]} 0%, {COLOR_PALETTE["success_dark"]} 100%); height: 100%; width: {bar_filled_width}%; transition: width 0.8s cubic-bezier(0.4, 0, 0.2, 1); position: relative; overflow: hidden; box-shadow: 0 0 10px rgba(16, 185, 129, 0.5);">')
        lines.append(f'        <div style="position: absolute; top: 0; left: 0; right: 0; bottom: 0; background: linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.3) 50%, transparent 100%); animation: shimmer 2s infinite;"></div>')
        lines.append(f'      </div>')
        lines.append(f'    </div>')
        lines.append(f'  </div>')

        # 습득 경로
        if evidence:
            lines.append(f'  <div style="background: rgba(0,0,0,0.2); padding: 12px; border-radius: 4px;">')
            lines.append(f'    <div style="font-weight: bold; margin-bottom: 8px;">📚 습득 경로</div>')
            lines.append(f'    <ol style="margin: 0; padding-left: 20px;">')
            for ev in evidence:  # 모든 증거 표시 (제한 제거)
                lines.append(f'      <li style="margin-bottom: 4px; opacity: 0.95; word-wrap: break-word; overflow-wrap: break-word; white-space: pre-wrap; line-height: 1.6;">{ev}</li>')
            lines.append(f'    </ol>')
            lines.append(f'  </div>')

        lines.append('</div>')
        lines.append("")

        return lines

    @staticmethod
    def _convert_markdown_links_to_html(text: str) -> str:
        """마크다운 링크를 HTML 링크로 변환.

        Args:
            text: 변환할 텍스트 (마크다운 링크 포함 가능)

        Returns:
            HTML 링크로 변환된 텍스트
        """
        import re
        # 마크다운 링크 패턴: [텍스트](URL)
        pattern = r'\[([^\]]+)\]\(([^\)]+)\)'
        # HTML 링크로 변환: <a href="URL">텍스트</a>
        return re.sub(pattern, r'<a href="\2" target="_blank" style="color: #3b82f6; text-decoration: underline;">\1</a>', text)

    @staticmethod
    def render_skill_tree_table(
        acquired_skills: List[Dict[str, Any]],
        growing_skills: List[Dict[str, Any]],
        available_skills: List[Dict[str, Any]]
    ) -> List[str]:
        """스킬 트리를 하나의 HTML 테이블로 통합 렌더링.

        Args:
            acquired_skills: 획득한 스킬 리스트 (각 항목은 {"name": str, "type": str, "mastery": int, "effect": str, "evidence": List[str], "emoji": str})
            growing_skills: 성장 중인 스킬 리스트
            available_skills: 습득 가능한 스킬 리스트

        Returns:
            마크다운 라인 리스트
        """
        lines = []

        # 테이블 헤더
        headers = ["구분", "스킬명", "레벨", "마스터리", "효과", "증거/습득경로"]
        rows = []

        # 타입 이모지 매핑
        type_emojis = {
            "패시브": "🟢",
            "액티브": "🔵",
            "성장중": "🟡",
            "미습득": "🔴"
        }

        def _sanitize(text: str) -> str:
            return html.escape(text, quote=False)

        def _build_evidence(evidence_list: List[str]) -> str:
            evidence_html = "<br>".join(
                [
                    f"• {GameRenderer._convert_markdown_links_to_html(_sanitize(ev))}"
                    for ev in evidence_list[:5]
                ]
            )
            if len(evidence_list) > 5:
                evidence_html += f"<br>... 외 {len(evidence_list) - 5}개"
            return evidence_html

        def _render_row(
            prefix: str,
            skill: Dict[str, Any],
            default_type: str,
            mastery_default: int,
            bar_colors: Tuple[str, str]
        ) -> None:
            mastery = skill.get("mastery", mastery_default)
            stars = min(5, mastery // 20)
            star_display = "★" * stars + "☆" * (5 - stars)
            level = min(5, (mastery // 20) + 1)

            skill_type_raw = skill.get("type", default_type)
            skill_type = _sanitize(skill_type_raw)
            type_emoji = type_emojis.get(skill_type_raw, "⚪")
            skill_name = _sanitize(skill.get("name", ""))

            mastery_bar = (
                f'<div style="background: {COLOR_PALETTE["gray_200"]}; border-radius: 6px; height: 10px; overflow: hidden; position: relative; box-shadow: inset 0 1px 3px rgba(0,0,0,0.1);">'
                f'<div style="background: linear-gradient(90deg, {bar_colors[0]} 0%, {bar_colors[1]} 100%); height: 100%; width: {mastery}%; transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1); box-shadow: 0 0 8px rgba(16, 185, 129, 0.4);"></div>'
                "</div>"
            )
            mastery_display = f'<span style="font-weight: bold; color: {bar_colors[1]};">{mastery}%</span><br>{mastery_bar}'

            evidence_list = skill.get("evidence", []) or []
            evidence_html = _build_evidence(evidence_list)

            effect_text = _sanitize(skill.get("effect", ""))

            rows.append([
                prefix,
                f'{skill.get("emoji", "💠")} <strong>{skill_name}</strong>',
                f'Lv.{level}<br>{star_display}',
                mastery_display,
                f'{type_emoji} {skill_type}<br><span style="color: #6b7280; font-size: 0.9em;">{GameRenderer._convert_markdown_links_to_html(effect_text)}</span>',
                evidence_html if evidence_html else "-",
            ])

        for skill in acquired_skills:
            _render_row('💎 <strong>획득</strong>', skill, "패시브", 0, ("#4ade80", "#22c55e"))

        for skill in growing_skills:
            _render_row('🌱 <strong>성장중</strong>', skill, "성장중", 60, ("#fbbf24", "#f59e0b"))

        for skill in available_skills:
            _render_row('🎯 <strong>습득 가능</strong>', skill, "미습득", 40, ("#ef4444", "#dc2626"))

        # HTML 테이블 렌더링
        if rows:
            lines.extend(GameRenderer.render_html_table(
                headers=headers,
                rows=rows,
                title="",
                description="",
                striped=True,
                escape_cells=False
            ))

        return lines

    @staticmethod
    def render_character_stats(
        level: int,
        title: str,
        rank_emoji: str,
        specialty_title: str,
        stats: Dict[str, int],
        experience_data: Dict[str, int],
        badges: List[str],
        use_tier_system: bool = False
    ) -> List[str]:
        """RPG 스타일 캐릭터 스탯 시각화 렌더링 (HTML 테이블 사용).

        Args:
            level: 레벨 (1-99) 또는 티어 (1-6)
            title: 레벨 타이틀 (예: "마스터", "그랜드마스터")
            rank_emoji: 랭크 이모지 (예: "👑", "🏆")
            specialty_title: 특성 타이틀 (예: "코드 아키텍트")
            stats: 능력치 딕셔너리 {"code_quality": 85, ...}
            experience_data: 경험치 데이터 딕셔너리
            badges: 획득한 뱃지 리스트
            use_tier_system: True면 "Tier X", False면 "Lv.X" 표시

        Returns:
            마크다운 라인 리스트
        """
        lines = []
        avg_stat = sum(stats.values()) / len(stats) if stats else 0

        # HTML 캐릭터 스탯 카드
        lines.append('<div style="border: 3px solid #2d3748; border-radius: 12px; padding: 20px; margin: 20px 0; background: linear-gradient(135deg, #1a202c 0%, #2d3748 100%); color: white; font-family: \'Segoe UI\', Tahoma, Geneva, Verdana, sans-serif; box-shadow: 0 4px 6px rgba(0,0,0,0.3);">')

        # 헤더: 레벨, 타이틀, 파워
        level_display = f"Tier {level}" if use_tier_system else f"Lv.{level}"
        lines.append(f'  <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; padding-bottom: 16px; border-bottom: 2px solid #4a5568;">')
        lines.append(f'    <div>')
        lines.append(f'      <div style="font-size: 1.5em; font-weight: bold;">{rank_emoji} {level_display}: {title}</div>')
        lines.append(f'      <div style="font-size: 1.1em; color: #fbbf24; margin-top: 4px;">🏅 특성: {specialty_title}</div>')
        lines.append(f'    </div>')
        lines.append(f'    <div style="text-align: right;">')
        lines.append(f'      <div style="font-size: 0.9em; color: #cbd5e0;">총 파워</div>')
        lines.append(f'      <div style="font-size: 2em; font-weight: bold; color: #48bb78;">{int(avg_stat)}<span style="font-size: 0.6em; color: #cbd5e0;">/100</span></div>')
        lines.append(f'    </div>')
        lines.append(f'  </div>')

        # 능력치 현황
        lines.append(f'  <div style="margin-bottom: 16px;">')
        lines.append(f'    <h4 style="margin: 0 0 12px 0; color: #e2e8f0; font-size: 1.1em;">⚔️ 능력치 현황</h4>')

        # 각 스탯 렌더링
        stat_emojis = {
            "code_quality": "💻",
            "collaboration": "🤝",
            "problem_solving": "🧩",
            "productivity": "⚡",
            "consistency": "📅",
            "growth": "📈",
        }

        stat_names_kr = {
            "code_quality": "코드 품질",
            "collaboration": "협업력",
            "problem_solving": "문제 해결력",
            "productivity": "생산성",
            "consistency": "꾸준함",
            "growth": "성장성",
        }

        # 스탯 색상 정의
        stat_colors = {
            "code_quality": "#3b82f6",  # 파란색
            "collaboration": "#8b5cf6",  # 보라색
            "problem_solving": "#ec4899",  # 핑크색
            "productivity": "#f59e0b",  # 주황색
            "consistency": "#f97316",  # 진한 주황
            "growth": "#10b981",  # 초록색
        }

        for stat_key, stat_value in stats.items():
            stat_name = stat_names_kr.get(stat_key, stat_key)
            emoji = stat_emojis.get(stat_key, "📊")
            color = stat_colors.get(stat_key, "#6b7280")

            lines.append(f'    <div style="margin-bottom: 14px;">')
            lines.append(f'      <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">')
            lines.append(f'        <span style="font-weight: bold; font-size: 0.95em;">{emoji} {stat_name}</span>')
            lines.append(f'        <span style="font-weight: bold; color: {color}; font-size: 0.95em;">{stat_value}/100</span>')
            lines.append(f'      </div>')
            lines.append(f'      <div style="background: rgba(255,255,255,0.1); border-radius: 12px; height: 18px; overflow: hidden; position: relative; box-shadow: inset 0 2px 4px rgba(0,0,0,0.3);">')
            lines.append(f'        <div style="background: linear-gradient(90deg, {color} 0%, {color}dd 100%); height: 100%; width: {stat_value}%; transition: width 0.8s cubic-bezier(0.4, 0, 0.2, 1); position: relative; overflow: hidden; box-shadow: 0 0 12px {color}80;">')
            lines.append(f'          <div style="position: absolute; top: 0; left: 0; right: 0; bottom: 0; background: linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.2) 50%, transparent 100%); animation: shimmer 2.5s infinite;"></div>')
            lines.append(f'        </div>')
            lines.append(f'      </div>')
            lines.append(f'    </div>')

        lines.append(f'  </div>')

        # 경험치 데이터
        if experience_data:
            lines.append(f'  <div style="background: rgba(255,255,255,0.05); padding: 12px; border-radius: 8px; margin-bottom: 16px;">')
            lines.append(f'    <h4 style="margin: 0 0 8px 0; color: #e2e8f0;">✨ 획득 경험치</h4>')
            lines.append(f'    <table style="width: 100%; border-collapse: collapse;">')

            for key, value in experience_data.items():
                lines.append(f'      <tr>')
                lines.append(f'        <td style="padding: 6px 0; color: #cbd5e0;">{key}</td>')
                # Format numbers with commas, but keep strings as-is
                formatted_value = f'{value:,}' if isinstance(value, int) else value
                lines.append(f'        <td style="padding: 6px 0; text-align: right; font-weight: bold; color: #fbbf24;">{formatted_value}</td>')
                lines.append(f'      </tr>')

            lines.append(f'    </table>')
            lines.append(f'  </div>')

        lines.append('</div>')
        lines.append("")

        # 뱃지 표시 (HTML 뱃지 스타일)
        if badges:
            lines.append('<div style="margin: 16px 0;">')
            lines.append('  <h4 style="color: #2d3748; margin-bottom: 12px;">🎖️ 획득한 뱃지</h4>')
            lines.append('  <div style="display: flex; flex-wrap: wrap; gap: 8px;">')

            for badge in badges:
                lines.append(f'    <span style="display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 6px 12px; border-radius: 16px; font-size: 0.9em; font-weight: 500; box-shadow: 0 2px 4px rgba(0,0,0,0.2);">{badge}</span>')

            lines.append('  </div>')
            lines.append('</div>')
            lines.append("")

        return lines

    @staticmethod
    def render_html_table(
        headers: List[str],
        rows: List[List[str]],
        title: str = "",
        description: str = "",
        striped: bool = True,
        escape_cells: bool = True
    ) -> List[str]:
        """범용 HTML 테이블 렌더링.

        Args:
            headers: 테이블 헤더 리스트
            rows: 테이블 행 데이터 (각 행은 문자열 리스트)
            title: 테이블 제목 (선택)
            description: 테이블 설명 (선택)
            striped: 줄무늬 스타일 적용 여부
            escape_cells: True면 각 셀을 HTML 이스케이프하여 렌더링

        Returns:
            마크다운 라인 리스트
        """
        lines = []

        # 컨테이너 시작
        lines.append('<div style="border: 2px solid #e2e8f0; border-radius: 8px; padding: 16px; margin: 16px 0; background: white; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">')

        # 제목 및 설명
        if title:
            lines.append(f'  <h4 style="margin: 0 0 8px 0; color: #2d3748; font-size: 1.2em;">{title}</h4>')
        if description:
            lines.append(f'  <p style="margin: 0 0 12px 0; color: #718096; font-size: 0.9em;">{description}</p>')

        # 테이블 시작
        lines.append('  <table style="width: 100%; border-collapse: collapse; font-size: 0.95em;">')

        # 헤더
        lines.append('    <thead>')
        lines.append('      <tr style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;">')
        for header in headers:
            lines.append(f'        <th style="padding: 12px; text-align: left; font-weight: 600;">{header}</th>')
        lines.append('      </tr>')
        lines.append('    </thead>')

        # 바디
        lines.append('    <tbody>')
        for idx, row in enumerate(rows):
            bg_color = '#f7fafc' if striped and idx % 2 == 0 else 'white'
            lines.append(f'      <tr style="background: {bg_color}; border-bottom: 1px solid #e2e8f0;">')
            for cell in row:
                cell_content = str(cell)
                if escape_cells:
                    cell_content = html.escape(cell_content)
                cell_with_links = GameRenderer._convert_markdown_links_to_html(cell_content)
                lines.append(f'        <td style="padding: 10px; color: #2d3748;">{cell_with_links}</td>')
            lines.append('      </tr>')
        lines.append('    </tbody>')

        lines.append('  </table>')
        lines.append('</div>')
        lines.append("")

        return lines

    @staticmethod
    def render_metric_cards(
        metrics: List[Dict[str, str]],
        columns: int = 3
    ) -> List[str]:
        """메트릭 카드 그리드 렌더링.

        Args:
            metrics: 메트릭 딕셔너리 리스트
                    각 딕셔너리는 {"title": "...", "value": "...", "emoji": "...", "color": "#..."}
            columns: 열 개수 (기본 3)

        Returns:
            마크다운 라인 리스트
        """
        lines = []

        # 그리드 컨테이너
        lines.append(f'<div style="display: grid; grid-template-columns: repeat({columns}, 1fr); gap: 16px; margin: 16px 0;">')

        for metric in metrics:
            title = metric.get("title", "")
            value = metric.get("value", "")
            emoji = metric.get("emoji", "📊")
            color = metric.get("color", "#667eea")

            # 카드
            lines.append('  <div style="border: 2px solid #e2e8f0; border-radius: 8px; padding: 16px; background: white; box-shadow: 0 2px 4px rgba(0,0,0,0.1); text-align: center;">')
            lines.append(f'    <div style="font-size: 2em; margin-bottom: 8px;">{emoji}</div>')
            lines.append(f'    <div style="font-size: 0.9em; color: #718096; margin-bottom: 4px;">{title}</div>')
            lines.append(f'    <div style="font-size: 1.8em; font-weight: bold; color: {color};">{value}</div>')
            lines.append('  </div>')

        lines.append('</div>')
        lines.append("")

        return lines

    @staticmethod
    def render_info_box(
        title: str,
        content: str,
        emoji: str = "💡",
        bg_color: str = "#eef2ff",
        border_color: str = "#667eea"
    ) -> List[str]:
        """정보 박스 렌더링.

        Args:
            title: 박스 제목
            content: 박스 내용
            emoji: 이모지
            bg_color: 배경색
            border_color: 테두리 색

        Returns:
            마크다운 라인 리스트
        """
        lines = []

        lines.append(f'<div style="border-left: 4px solid {border_color}; background: {bg_color}; padding: 16px; margin: 16px 0; border-radius: 4px;">')
        lines.append(f'  <div style="display: flex; align-items: center; margin-bottom: 8px;">')
        lines.append(f'    <span style="font-size: 1.5em; margin-right: 8px;">{emoji}</span>')
        lines.append(f'    <h4 style="margin: 0; color: #2d3748; font-size: 1.1em;">{title}</h4>')
        lines.append(f'  </div>')
        lines.append(f'  <div style="color: #4a5568; line-height: 1.6; white-space: pre-wrap;">{content}</div>')
        lines.append('</div>')
        lines.append("")

        return lines

    @staticmethod
    def render_awards_grid(
        awards: List[Dict[str, str]],
        columns: int = 2
    ) -> List[str]:
        """어워즈 그리드 렌더링.

        Args:
            awards: 어워즈 딕셔너리 리스트
                   각 딕셔너리는 {"category": "...", "description": "...", "emoji": "...", "count": "..."}
            columns: 열 개수

        Returns:
            마크다운 라인 리스트
        """
        lines = []

        lines.append(f'<div style="display: grid; grid-template-columns: repeat({columns}, 1fr); gap: 16px; margin: 16px 0;">')

        for award in awards:
            category = award.get("category", "")
            description = award.get("description", "")
            emoji = award.get("emoji", "🏆")
            count = award.get("count", "0")

            # 어워드 카드
            lines.append('  <div style="border: 2px solid #fbbf24; border-radius: 8px; padding: 16px; background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%); box-shadow: 0 2px 4px rgba(251, 191, 36, 0.3);">')
            lines.append(f'    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">')
            lines.append(f'      <span style="font-size: 2em;">{emoji}</span>')
            lines.append(f'      <span style="background: #f59e0b; color: white; padding: 4px 8px; border-radius: 12px; font-size: 0.85em; font-weight: bold;">{count}</span>')
            lines.append(f'    </div>')
            lines.append(f'    <h4 style="margin: 0 0 4px 0; color: #78350f; font-size: 1.1em;">{category}</h4>')
            lines.append(f'    <p style="margin: 0; color: #92400e; font-size: 0.9em; line-height: 1.4;">{description}</p>')
            lines.append('  </div>')

        lines.append('</div>')
        lines.append("")

        return lines

    @staticmethod
    def render_monthly_chart(
        monthly_data: List[Dict[str, Any]],
        title: str = "월별 활동 트렌드",
        value_key: str = "count",
        label_key: str = "month"
    ) -> List[str]:
        """월별 차트 렌더링 (세로 막대 그래프 스타일).

        Args:
            monthly_data: 월별 데이터 리스트 [{"month": "2024-01", "count": 10}, ...]
            title: 차트 제목
            value_key: 값 키 이름
            label_key: 레이블 키 이름

        Returns:
            마크다운 라인 리스트
        """
        lines = []

        if not monthly_data:
            return lines

        # 최대값 찾기
        max_value = max((item.get(value_key, 0) for item in monthly_data), default=1)
        if max_value == 0:
            max_value = 1

        # 차트 컨테이너
        lines.append('<div style="border: 2px solid #e2e8f0; border-radius: 8px; padding: 20px; margin: 16px 0; background: white; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">')
        lines.append(f'  <h4 style="margin: 0 0 16px 0; color: #2d3748; font-size: 1.2em;">{title}</h4>')

        # 차트 영역
        lines.append('  <div style="display: flex; align-items: flex-end; justify-content: space-around; height: 200px; border-bottom: 2px solid #cbd5e0; padding: 0 8px;">')

        for item in monthly_data:
            label = item.get(label_key, "")
            value = item.get(value_key, 0)
            height_percent = (value / max_value) * 100 if max_value > 0 else 0

            # 막대 및 레이블
            lines.append('    <div style="display: flex; flex-direction: column; align-items: center; flex: 1; margin: 0 4px;">')
            lines.append(f'      <div style="font-size: 0.8em; font-weight: bold; color: #4a5568; margin-bottom: 4px;">{value}</div>')
            lines.append(f'      <div style="width: 100%; max-width: 60px; background: linear-gradient(180deg, #667eea 0%, #764ba2 100%); border-radius: 4px 4px 0 0; height: {height_percent}%; min-height: 4px;"></div>')
            lines.append(f'      <div style="font-size: 0.75em; color: #718096; margin-top: 8px; transform: rotate(-45deg); white-space: nowrap;">{label}</div>')
            lines.append('    </div>')

        lines.append('  </div>')
        lines.append('</div>')
        lines.append("")

        return lines

    @staticmethod
    def render_line_chart(
        data_points: List[Dict[str, Any]],
        title: str = "추세 분석",
        x_key: str = "label",
        y_key: str = "value",
        color: str = None
    ) -> List[str]:
        """라인 차트 렌더링 (월별 트렌드 등에 사용).

        Args:
            data_points: 데이터 포인트 리스트 [{"label": "Jan", "value": 10}, ...]
            title: 차트 제목
            x_key: X축 데이터 키
            y_key: Y축 데이터 키
            color: 라인 색상 (기본값: primary)

        Returns:
            마크다운 라인 리스트
        """
        if not data_points:
            return []

        lines = []
        line_color = color or COLOR_PALETTE["primary"]

        # 최대값 찾기
        max_value = max((item.get(y_key, 0) for item in data_points), default=1)
        if max_value == 0:
            max_value = 1

        # 차트 컨테이너
        lines.append('<div style="border: 2px solid ' + COLOR_PALETTE["gray_200"] + '; border-radius: 12px; padding: 24px; margin: 16px 0; background: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">')
        lines.append(f'  <h4 style="margin: 0 0 20px 0; color: {COLOR_PALETTE["gray_800"]}; font-size: 1.3em;">{title}</h4>')

        # SVG 라인 차트
        width = 800
        height = 300
        padding = 40
        chart_width = width - 2 * padding
        chart_height = height - 2 * padding

        lines.append(f'  <svg width="100%" height="{height}" viewBox="0 0 {width} {height}" style="overflow: visible;">')

        # 배경 그리드
        for i in range(5):
            y = padding + (chart_height / 4) * i
            lines.append(f'    <line x1="{padding}" y1="{y}" x2="{width - padding}" y2="{y}" stroke="{COLOR_PALETTE["gray_200"]}" stroke-width="1" stroke-dasharray="5,5"/>')

        # 데이터 포인트 계산
        num_points = len(data_points)
        x_step = chart_width / (num_points - 1) if num_points > 1 else 0

        # 라인 패스 생성
        path_points = []
        for idx, item in enumerate(data_points):
            value = item.get(y_key, 0)
            x = padding + idx * x_step
            y = padding + chart_height - (value / max_value * chart_height)
            path_points.append(f"{x},{y}")

        path_d = "M " + " L ".join(path_points)

        # 그라데이션 영역
        area_points = path_points + [
            f"{width - padding},{padding + chart_height}",
            f"{padding},{padding + chart_height}"
        ]
        area_d = "M " + " L ".join(area_points) + " Z"

        # 그라데이션 정의
        lines.append(f'    <defs>')
        lines.append(f'      <linearGradient id="lineGradient" x1="0%" y1="0%" x2="0%" y2="100%">')
        lines.append(f'        <stop offset="0%" style="stop-color:{line_color};stop-opacity:0.3" />')
        lines.append(f'        <stop offset="100%" style="stop-color:{line_color};stop-opacity:0.05" />')
        lines.append(f'      </linearGradient>')
        lines.append(f'    </defs>')

        # 영역 채우기
        lines.append(f'    <path d="{area_d}" fill="url(#lineGradient)"/>')

        # 라인 그리기
        lines.append(f'    <path d="{path_d}" fill="none" stroke="{line_color}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>')

        # 데이터 포인트 및 레이블
        for idx, item in enumerate(data_points):
            value = item.get(y_key, 0)
            label = item.get(x_key, "")
            x = padding + idx * x_step
            y = padding + chart_height - (value / max_value * chart_height)

            # 포인트
            lines.append(f'    <circle cx="{x}" cy="{y}" r="5" fill="white" stroke="{line_color}" stroke-width="3"/>')

            # X축 레이블
            lines.append(f'    <text x="{x}" y="{height - 10}" text-anchor="middle" fill="{COLOR_PALETTE["gray_600"]}" font-size="12">{label}</text>')

        lines.append('  </svg>')
        lines.append('</div>')
        lines.append("")

        return lines

    @staticmethod
    def render_donut_chart(
        segments: List[Dict[str, Any]],
        title: str = "분포 현황",
        label_key: str = "label",
        value_key: str = "value",
        color_key: str = "color"
    ) -> List[str]:
        """도넛 차트 렌더링 (비율 데이터 시각화).

        Args:
            segments: 세그먼트 리스트 [{"label": "Python", "value": 45, "color": "#3b82f6"}, ...]
            title: 차트 제목
            label_key: 레이블 키
            value_key: 값 키
            color_key: 색상 키

        Returns:
            마크다운 라인 리스트
        """
        if not segments:
            return []

        lines = []

        # 총합 계산
        total = sum(seg.get(value_key, 0) for seg in segments)
        if total == 0:
            return []

        # 차트 컨테이너
        lines.append('<div style="border: 2px solid ' + COLOR_PALETTE["gray_200"] + '; border-radius: 12px; padding: 24px; margin: 16px 0; background: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">')
        lines.append(f'  <h4 style="margin: 0 0 20px 0; color: {COLOR_PALETTE["gray_800"]}; font-size: 1.3em;">{title}</h4>')
        lines.append('  <div style="display: flex; align-items: center; justify-content: space-around; flex-wrap: wrap;">')

        # SVG 도넛 차트
        size = 300
        center = size / 2
        radius = 100
        inner_radius = 60

        lines.append(f'    <svg width="{size}" height="{size}" viewBox="0 0 {size} {size}">')

        # 세그먼트 그리기
        current_angle = -90  # 12시 방향부터 시작

        for seg in segments:
            value = seg.get(value_key, 0)
            percentage = (value / total) * 100
            angle = (value / total) * 360

            # 색상 (기본값 사용)
            seg_color = seg.get(color_key, COLOR_PALETTE["primary"])

            # 시작 각도와 끝 각도 계산 (라디안)
            start_angle_rad = current_angle * 3.14159 / 180
            end_angle_rad = (current_angle + angle) * 3.14159 / 180

            # 호의 좌표 계산
            x1 = center + radius * __import__('math').cos(start_angle_rad)
            y1 = center + radius * __import__('math').sin(start_angle_rad)
            x2 = center + radius * __import__('math').cos(end_angle_rad)
            y2 = center + radius * __import__('math').sin(end_angle_rad)

            x3 = center + inner_radius * __import__('math').cos(end_angle_rad)
            y3 = center + inner_radius * __import__('math').sin(end_angle_rad)
            x4 = center + inner_radius * __import__('math').cos(start_angle_rad)
            y4 = center + inner_radius * __import__('math').sin(start_angle_rad)

            # 큰 호 플래그
            large_arc = 1 if angle > 180 else 0

            # 패스 생성
            path_d = f"M {x1},{y1} A {radius},{radius} 0 {large_arc},1 {x2},{y2} L {x3},{y3} A {inner_radius},{inner_radius} 0 {large_arc},0 {x4},{y4} Z"

            lines.append(f'      <path d="{path_d}" fill="{seg_color}" stroke="white" stroke-width="2" opacity="0.9">')
            lines.append(f'        <title>{seg.get(label_key, "")}: {percentage:.1f}%</title>')
            lines.append(f'      </path>')

            current_angle += angle

        # 중앙 텍스트
        lines.append(f'      <text x="{center}" y="{center - 10}" text-anchor="middle" fill="{COLOR_PALETTE["gray_800"]}" font-size="24" font-weight="bold">{total}</text>')
        lines.append(f'      <text x="{center}" y="{center + 15}" text-anchor="middle" fill="{COLOR_PALETTE["gray_600"]}" font-size="14">Total</text>')

        lines.append('    </svg>')

        # 범례
        lines.append('    <div style="display: flex; flex-direction: column; gap: 12px;">')
        for seg in segments:
            value = seg.get(value_key, 0)
            label = seg.get(label_key, "")
            seg_color = seg.get(color_key, COLOR_PALETTE["primary"])
            percentage = (value / total) * 100

            lines.append('      <div style="display: flex; align-items: center; gap: 12px;">')
            lines.append(f'        <div style="width: 20px; height: 20px; background: {seg_color}; border-radius: 4px;"></div>')
            lines.append(f'        <div style="flex: 1;">')
            lines.append(f'          <div style="font-weight: bold; color: {COLOR_PALETTE["gray_800"]};">{label}</div>')
            lines.append(f'          <div style="color: {COLOR_PALETTE["gray_600"]}; font-size: 0.9em;">{value} ({percentage:.1f}%)</div>')
            lines.append(f'        </div>')
            lines.append('      </div>')

        lines.append('    </div>')
        lines.append('  </div>')
        lines.append('</div>')
        lines.append("")

        return lines

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

    @staticmethod
    def render_loading_skeleton(
        num_rows: int = 3,
        title: str = "로딩 중..."
    ) -> List[str]:
        """스켈레톤 로딩 UI 렌더링.

        Args:
            num_rows: 스켈레톤 행 개수
            title: 로딩 메시지

        Returns:
            마크다운 라인 리스트
        """
        lines = []

        lines.append(f'<div style="border: 2px solid {COLOR_PALETTE["gray_200"]}; border-radius: 12px; padding: 24px; margin: 16px 0; background: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">')
        lines.append(f'  <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 20px;">')
        lines.append(f'    <div class="skeleton" style="width: 40px; height: 40px; border-radius: 50%;"></div>')
        lines.append(f'    <div style="flex: 1;">')
        lines.append(f'      <div style="font-weight: bold; color: {COLOR_PALETTE["gray_600"]};">{title}</div>')
        lines.append(f'    </div>')
        lines.append(f'  </div>')

        for _ in range(num_rows):
            lines.append(f'  <div class="skeleton" style="height: 20px; margin-bottom: 12px; border-radius: 4px;"></div>')

        lines.append('</div>')
        lines.append("")

        return lines

    @staticmethod
    def render_progress_indicator(
        current: int,
        total: int,
        label: str = "진행 중...",
        show_percentage: bool = True
    ) -> List[str]:
        """프로그레스 인디케이터 렌더링 (보고서 생성 진행 상황 표시).

        Args:
            current: 현재 진행 값
            total: 전체 값
            label: 진행 레이블
            show_percentage: 백분율 표시 여부

        Returns:
            마크다운 라인 리스트
        """
        lines = []

        percentage = (current / total * 100) if total > 0 else 0

        lines.append(f'<div style="border: 2px solid {COLOR_PALETTE["primary"]}; border-radius: 12px; padding: 24px; margin: 16px 0; background: linear-gradient(135deg, {COLOR_PALETTE["bg_gradient_purple_start"]}15 0%, {COLOR_PALETTE["bg_gradient_purple_end"]}15 100%); box-shadow: 0 4px 6px rgba(0,0,0,0.1);">')

        # 레이블 및 카운터
        lines.append(f'  <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">')
        lines.append(f'    <div style="font-weight: bold; color: {COLOR_PALETTE["gray_800"]}; font-size: 1.1em;">{label}</div>')
        if show_percentage:
            lines.append(f'    <div style="font-weight: bold; color: {COLOR_PALETTE["primary"]}; font-size: 1.2em;">{int(percentage)}%</div>')
        else:
            lines.append(f'    <div style="color: {COLOR_PALETTE["gray_600"]}; font-size: 0.95em;">{current} / {total}</div>')
        lines.append(f'  </div>')

        # 프로그레스 바
        lines.append(f'  <div style="background: {COLOR_PALETTE["gray_200"]}; border-radius: 12px; height: 24px; overflow: hidden; position: relative; box-shadow: inset 0 2px 4px rgba(0,0,0,0.1);">')
        lines.append(f'    <div style="background: linear-gradient(90deg, {COLOR_PALETTE["primary"]} 0%, {COLOR_PALETTE["secondary"]} 100%); height: 100%; width: {percentage}%; transition: width 0.5s cubic-bezier(0.4, 0, 0.2, 1); position: relative; overflow: hidden; box-shadow: 0 0 15px {COLOR_PALETTE["primary"]}60;">')
        lines.append(f'      <div style="position: absolute; top: 0; left: 0; right: 0; bottom: 0; background: linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.4) 50%, transparent 100%); animation: shimmer 1.5s infinite;"></div>')
        lines.append(f'    </div>')
        lines.append(f'  </div>')

        # 상세 정보
        lines.append(f'  <div style="margin-top: 12px; text-align: center; color: {COLOR_PALETTE["gray_600"]}; font-size: 0.9em;">')
        lines.append(f'    처리 중: {current} / {total} 항목 완료')
        lines.append(f'  </div>')

        lines.append('</div>')
        lines.append("")

        return lines

    @staticmethod
    def render_spinner(
        message: str = "처리 중...",
        size: int = 40
    ) -> List[str]:
        """스피너 애니메이션 렌더링.

        Args:
            message: 스피너와 함께 표시할 메시지
            size: 스피너 크기 (픽셀)

        Returns:
            마크다운 라인 리스트
        """
        lines = []

        lines.append('<div style="display: flex; align-items: center; justify-content: center; padding: 40px; margin: 20px 0;">')
        lines.append(f'  <div style="display: flex; flex-direction: column; align-items: center; gap: 16px;">')

        # SVG 스피너
        lines.append(f'    <svg width="{size}" height="{size}" viewBox="0 0 {size} {size}" xmlns="http://www.w3.org/2000/svg">')
        lines.append(f'      <circle cx="{size/2}" cy="{size/2}" r="{size/2 - 4}" stroke="{COLOR_PALETTE["gray_200"]}" stroke-width="4" fill="none"/>')
        lines.append(f'      <circle cx="{size/2}" cy="{size/2}" r="{size/2 - 4}" stroke="{COLOR_PALETTE["primary"]}" stroke-width="4" fill="none" stroke-dasharray="{size * 1.5} {size * 3}" stroke-linecap="round" style="animation: spin 1s linear infinite; transform-origin: center;">')
        lines.append('        <animateTransform attributeName="transform" type="rotate" from="0 20 20" to="360 20 20" dur="1s" repeatCount="indefinite"/>')
        lines.append('      </circle>')
        lines.append('    </svg>')

        # 메시지
        lines.append(f'    <div style="font-weight: 500; color: {COLOR_PALETTE["gray_700"]}; font-size: 1.1em;">{message}</div>')

        lines.append('  </div>')
        lines.append('</div>')
        lines.append("")

        # CSS for spin animation
        lines.append('<style>')
        lines.append('@keyframes spin {')
        lines.append('  from { transform: rotate(0deg); }')
        lines.append('  to { transform: rotate(360deg); }')
        lines.append('}')
        lines.append('</style>')
        lines.append("")

        return lines


class LevelCalculator:
    """레벨 및 타이틀 계산 유틸리티."""

    # 종합 보고서용 99레벨 시스템
    LEVEL_99_TITLES = [
        (700, 99, "전설의 코드마스터", "👑"),
        (400, 80, "그랜드마스터", "💎"),
        (200, 60, "마스터", "🏆"),
        (100, 40, "전문가", "⭐"),
        (50, 20, "숙련자", "💫"),
        (20, 10, "초보자", "🌱"),
        (0, 1, "견습생", "✨"),
    ]

    # 개별/일반 보고서용 티어 시스템
    TIER_SYSTEM = [
        (95, 6, "그랜드마스터", "👑"),
        (80, 5, "마스터", "🏆"),
        (70, 4, "전문가", "⭐"),
        (55, 3, "숙련자", "💎"),
        (35, 2, "견습생", "🎓"),
        (0, 1, "초보자", "🌱"),
    ]

    # 특성 타이틀 매핑
    SPECIALTY_TITLES = {
        "코드 품질": "코드 아키텍트",
        "협업력": "팀 플레이어",
        "문제 해결력": "문제 해결사",
        "생산성": "스피드 러너",
        "꾸준함": "꾸준함의 달인",
        "성장성": "라이징 스타",
    }

    @staticmethod
    def calculate_level_99(total_activity: int) -> Tuple[int, str, str]:
        """99레벨 시스템으로 레벨 계산 (종합 보고서용).

        Args:
            total_activity: 총 활동량 (커밋 + PR + 기타)

        Returns:
            (레벨, 타이틀, 랭크 이모지) 튜플
        """
        for threshold, base_level, title, emoji in LevelCalculator.LEVEL_99_TITLES:
            if total_activity >= threshold:
                # 세밀한 레벨 계산
                if threshold == 700:
                    level = 99
                elif threshold == 400:
                    level = min(99, 80 + (total_activity - 400) // 20)
                elif threshold == 200:
                    level = min(99, 60 + (total_activity - 200) // 10)
                elif threshold == 100:
                    level = min(99, 40 + (total_activity - 100) // 5)
                elif threshold == 50:
                    level = min(99, 20 + (total_activity - 50) // 3)
                elif threshold == 20:
                    level = min(99, 10 + (total_activity - 20) // 2)
                else:
                    level = max(1, total_activity)

                return (level, title, emoji)

        return (1, "견습생", "✨")

    @staticmethod
    def calculate_tier(avg_stat: float) -> Tuple[int, str, str]:
        """티어 시스템으로 등급 계산 (개별/일반 보고서용).

        Args:
            avg_stat: 평균 스탯 (0-100)

        Returns:
            (티어, 타이틀, 랭크 이모지) 튜플
        """
        for threshold, tier, title, emoji in LevelCalculator.TIER_SYSTEM:
            if avg_stat >= threshold:
                return (tier, title, emoji)

        return (1, "초보자", "🌱")

    @staticmethod
    def get_specialty_title(stats: Dict[str, int]) -> str:
        """가장 높은 스탯을 기반으로 특성 타이틀 결정.

        Args:
            stats: 능력치 딕셔너리

        Returns:
            특성 타이틀 문자열
        """
        if not stats:
            return "개발자"

        stat_names_kr = {
            "code_quality": "코드 품질",
            "collaboration": "협업력",
            "problem_solving": "문제 해결력",
            "productivity": "생산성",
            "consistency": "꾸준함",
            "growth": "성장성",
        }

        # 가장 높은 스탯 찾기
        highest_stat = max(stats.items(), key=lambda x: x[1])
        primary_specialty = stat_names_kr.get(highest_stat[0], "")

        return LevelCalculator.SPECIALTY_TITLES.get(primary_specialty, "개발자")

    @staticmethod
    def get_badges_from_stats(
        stats: Dict[str, int],
        total_commits: int = 0,
        total_prs: int = 0,
        total_repos: int = 0
    ) -> List[str]:
        """스탯과 활동량에 따른 뱃지 생성.

        Args:
            stats: 능력치 딕셔너리
            total_commits: 총 커밋 수
            total_prs: 총 PR 수
            total_repos: 총 저장소 수

        Returns:
            뱃지 문자열 리스트
        """
        badges = []

        # 스탯 기반 뱃지 (85 이상으로 상향)
        if stats.get("code_quality", 0) >= 85:
            badges.append("🏅 코드 마스터")
        if stats.get("collaboration", 0) >= 85:
            badges.append("🤝 협업 챔피언")
        if stats.get("problem_solving", 0) >= 85:
            badges.append("🧠 문제 해결 전문가")
        if stats.get("productivity", 0) >= 85:
            badges.append("⚡ 생산성 괴물")
        if stats.get("growth", 0) >= 85:
            badges.append("🚀 급성장 개발자")

        # 활동량 기반 뱃지 (기준 상향)
        if total_commits >= 300:
            badges.append("💯 커밋 마라토너")
        elif total_commits >= 150:
            badges.append("📝 활발한 커미터")

        if total_prs >= 80:
            badges.append("🔀 PR 마스터")
        elif total_prs >= 30:
            badges.append("🔄 PR 컨트리뷰터")

        if total_repos >= 15:
            badges.append("🌐 멀티버스 탐험가")
        elif total_repos >= 8:
            badges.append("🗺️ 던전 크롤러")

        return badges


__all__ = ["GameRenderer", "LevelCalculator", "COLOR_PALETTE", "get_animation_styles"]
