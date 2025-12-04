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
    def get_trend_indicator(
        direction: str,
        percentage: float,
        size: str = "medium"
    ) -> str:
        """Get HTML for trend indicator with arrow and color.

        Args:
            direction: "up" or "down"
            percentage: Percentage value (positive number)
            size: "small", "medium", or "large"

        Returns:
            HTML string for trend indicator
        """
        # Size mappings
        sizes = {
            "small": {"font": "12px", "icon": "14px"},
            "medium": {"font": "14px", "icon": "16px"},
            "large": {"font": "16px", "icon": "20px"}
        }

        size_config = sizes.get(size, sizes["medium"])

        if direction == "up":
            color = COLOR_PALETTE["success"]
            arrow = "↑"
        else:
            color = COLOR_PALETTE["danger"]
            arrow = "↓"

        return f'<span style="color: {color}; font-size: {size_config["icon"]}; font-weight: 600;">{arrow} {percentage:.1f}%</span>'

    @staticmethod
    def get_trend_badge(
        label: str,
        value: float,
        trend_direction: str = None,
        trend_percentage: float = None
    ) -> str:
        """Get HTML for metric badge with optional trend.

        Args:
            label: Metric label
            value: Metric value
            trend_direction: Optional "up" or "down"
            trend_percentage: Optional percentage value

        Returns:
            HTML string for metric badge
        """
        trend_html = ""
        if trend_direction and trend_percentage is not None:
            if trend_direction == "up":
                color = COLOR_PALETTE["success"]
                arrow = "↑"
            else:
                color = COLOR_PALETTE["danger"]
                arrow = "↓"
            trend_html = f' <span style="color: {color}; font-size: 12px;">({arrow}{trend_percentage:.0f}%)</span>'

        return f'''<span style="
            display: inline-block;
            padding: 6px 12px;
            background: {COLOR_PALETTE["gray_100"]};
            border-radius: 6px;
            font-size: 14px;
            font-weight: 500;
            color: {COLOR_PALETTE["gray_800"]};
            margin: 4px;
        ">{label}: <strong>{value}</strong>{trend_html}</span>'''

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
        lines.append('<div class="skill-card">')

        # 스킬명 및 레벨
        lines.append(f'  <div class="skill-card-title">')
        lines.append(f'    {skill_emoji} {skill_name} <span class="skill-card-level-badge">Lv.{level}</span>')
        lines.append(f'  </div>')

        # 별 표시
        lines.append(f'  <div class="skill-card-stars">')
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
        lines.append(f'  <div class="skill-card-info-box">')
        lines.append(f'    <div class="skill-card-effect-title">💫 효과</div>')
        lines.append(f'    <div class="skill-card-effect-text">{effect_description}</div>')
        lines.append(f'  </div>')

        # 마스터리 바 (개선된 버전 with 애니메이션)
        lines.append(f'  <div class="progress-container">')
        lines.append(f'    <div class="progress-header">')
        lines.append(f'      <span class="progress-label">마스터리</span>')
        lines.append(f'      <span class="progress-value">{mastery_percentage}%</span>')
        lines.append(f'    </div>')
        lines.append(f'    <div class="progress-bar-bg">')
        lines.append(f'      <div class="progress-bar-fill" style="width: {bar_filled_width}%;">')
        lines.append(f'        <div class="progress-bar-shimmer"></div>')
        lines.append(f'      </div>')
        lines.append(f'    </div>')
        lines.append(f'  </div>')

        # 습득 경로
        if evidence:
            lines.append(f'  <div class="skill-card-info-box">')
            lines.append(f'    <div class="skill-card-effect-title">📚 습득 경로</div>')
            lines.append(f'    <ol style="margin: 0; padding-left: 20px;">')
            for ev in evidence:  # 모든 증거 표시 (제한 제거)
                lines.append(f'      <li class="skill-card-effect-text" style="margin-bottom: 4px;">{ev}</li>')
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
        lines.append('<div class="character-stats-card">')

        # 헤더: 레벨, 타이틀, 파워
        level_display = f"Tier {level}" if use_tier_system else f"Lv.{level}"
        lines.append(f'  <div class="character-header">')
        lines.append(f'    <div>')
        lines.append(f'      <div class="character-title">{rank_emoji} {level_display}: {title}</div>')
        lines.append(f'      <div class="character-specialty">🏅 특성: {specialty_title}</div>')
        lines.append(f'    </div>')
        lines.append(f'    <div class="text-right">')
        lines.append(f'      <div style="font-size: var(--font-size-sm); color: var(--color-gray-300);">총 파워</div>')
        lines.append(f'      <div class="character-power">{int(avg_stat)}<span style="font-size: 0.6em; color: var(--color-gray-300);">/100</span></div>')
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

            lines.append(f'    <div class="stat-item">')
            lines.append(f'      <div class="progress-header">')
            lines.append(f'        <span class="progress-label">{emoji} {stat_name}</span>')
            lines.append(f'        <span class="progress-value" style="color: {color};">{stat_value}/100</span>')
            lines.append(f'      </div>')
            lines.append(f'      <div class="stat-bar-bg">')
            lines.append(f'        <div class="progress-bar-fill" style="background: linear-gradient(90deg, {color} 0%, {color}dd 100%); width: {stat_value}%; box-shadow: 0 0 12px {color}80;">')
            lines.append(f'          <div class="progress-bar-shimmer"></div>')
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
        lines.append('<div class="table-container">')

        # 제목 및 설명
        if title:
            lines.append(f'  <h4>{title}</h4>')
        if description:
            lines.append(f'  <p style="margin: 0 0 var(--spacing-3) 0; color: var(--color-gray-600); font-size: var(--font-size-sm);">{description}</p>')

        # 테이블 시작
        lines.append('  <table class="report-table">')

        # 헤더
        lines.append('    <thead>')
        lines.append('      <tr>')
        for header in headers:
            lines.append(f'        <th>{header}</th>')
        lines.append('      </tr>')
        lines.append('    </thead>')

        # 바디
        lines.append('    <tbody>')
        for idx, row in enumerate(rows):
            lines.append(f'      <tr>')
            for cell in row:
                cell_content = str(cell)
                if escape_cells:
                    cell_content = html.escape(cell_content)
                cell_with_links = GameRenderer._convert_markdown_links_to_html(cell_content)
                lines.append(f'        <td>{cell_with_links}</td>')
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
        lines.append(f'<div class="metrics-grid">')

        for metric in metrics:
            title = metric.get("title", "")
            value = metric.get("value", "")
            emoji = metric.get("emoji", "📊")
            color = metric.get("color", "#667eea")

            # 카드
            lines.append('  <div class="metric-card hover-lift">')
            lines.append(f'    <div class="metric-emoji">{emoji}</div>')
            lines.append(f'    <div class="metric-title">{title}</div>')
            lines.append(f'    <div class="metric-value" style="color: {color};">{value}</div>')
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

        lines.append(f'<div class="info-box" style="border-left-color: {border_color}; background: {bg_color};">')
        lines.append(f'  <div class="info-box-header">')
        lines.append(f'    <span class="info-box-icon">{emoji}</span>')
        lines.append(f'    <h4 class="info-box-title">{title}</h4>')
        lines.append(f'  </div>')
        lines.append(f'  <div class="info-box-content">{content}</div>')
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

        lines.append(f'<div class="awards-grid">')

        for award in awards:
            category = award.get("category", "")
            description = award.get("description", "")
            emoji = award.get("emoji", "🏆")
            count = award.get("count", "0")

            # 어워드 카드
            lines.append('  <div class="award-card">')
            lines.append(f'    <div class="flex justify-between items-center mb-2">')
            lines.append(f'      <span style="font-size: var(--font-size-4xl);">{emoji}</span>')
            lines.append(f'      <span style="background: var(--color-warning-dark); color: white; padding: var(--spacing-1) var(--spacing-2); border-radius: var(--radius-full); font-size: var(--font-size-sm); font-weight: var(--font-weight-bold);">{count}</span>')
            lines.append(f'    </div>')
            lines.append(f'    <h4 style="margin: 0 0 var(--spacing-1) 0; color: #78350f; font-size: var(--font-size-lg);">{category}</h4>')
            lines.append(f'    <p style="margin: 0; color: #92400e; font-size: var(--font-size-sm); line-height: var(--line-height-normal);">{description}</p>')
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
        lines.append('<div class="chart-container">')
        lines.append(f'  <h4 class="chart-title">{title}</h4>')

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
        lines.append('<div class="chart-container">')
        lines.append(f'  <h4 class="chart-title">{title}</h4>')
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
    def render_radar_chart(
        stats: Dict[str, int],
        title: str = "능력치 레이더",
        size: int = 400
    ) -> List[str]:
        """레이더 차트 렌더링 (RPG 스타일 스탯 시각화).

        Args:
            stats: 스탯 딕셔너리 {"stat_name": value, ...} (0-100 범위)
            title: 차트 제목
            size: 차트 크기 (픽셀)

        Returns:
            마크다운 라인 리스트
        """
        if not stats:
            return []

        lines = []

        # 스탯 이름 매핑 (영문 -> 한글)
        stat_labels = {
            "code_quality": "코드 품질",
            "collaboration": "협업",
            "problem_solving": "문제해결",
            "productivity": "생산성",
            "consistency": "일관성",
            "growth": "성장"
        }

        # 스탯 색상 매핑
        stat_colors = {
            "code_quality": COLOR_PALETTE["stat_code_quality"],
            "collaboration": COLOR_PALETTE["stat_collaboration"],
            "problem_solving": COLOR_PALETTE["stat_problem_solving"],
            "productivity": COLOR_PALETTE["stat_productivity"],
            "consistency": COLOR_PALETTE["stat_consistency"],
            "growth": COLOR_PALETTE["stat_growth"]
        }

        # 차트 컨테이너
        lines.append('<div class="chart-container">')
        lines.append(f'  <h4 class="chart-title">{title}</h4>')
        lines.append('  <div style="display: flex; align-items: center; justify-content: center; flex-wrap: wrap; gap: var(--spacing-10);">')

        # SVG 레이더 차트
        center = size / 2
        max_radius = (size / 2) - 80  # 여백 확보

        lines.append(f'    <svg width="{size}" height="{size}" viewBox="0 0 {size} {size}">')

        # 배경 동심원 (20%, 40%, 60%, 80%, 100%)
        for i in range(5, 0, -1):
            radius = max_radius * (i / 5)
            opacity = 0.1 if i % 2 == 0 else 0.05
            lines.append(f'      <circle cx="{center}" cy="{center}" r="{radius}" fill="none" stroke="{COLOR_PALETTE["gray_300"]}" stroke-width="1" opacity="{opacity}"/>')
            # 레이블 (20, 40, 60, 80, 100)
            if i > 0:
                label_y = center - radius + 5
                lines.append(f'      <text x="{center + 5}" y="{label_y}" fill="{COLOR_PALETTE["gray_400"]}" font-size="10">{i * 20}</text>')

        # 스탯 축 그리기
        stat_items = list(stats.items())
        num_stats = len(stat_items)
        angle_step = 360 / num_stats

        # 축선 및 레이블
        for i, (stat_key, stat_value) in enumerate(stat_items):
            angle = (angle_step * i - 90) * 3.14159 / 180  # -90도로 12시 방향 시작

            # 축선
            end_x = center + max_radius * __import__('math').cos(angle)
            end_y = center + max_radius * __import__('math').sin(angle)
            lines.append(f'      <line x1="{center}" y1="{center}" x2="{end_x}" y2="{end_y}" stroke="{COLOR_PALETTE["gray_300"]}" stroke-width="1"/>')

            # 레이블 위치 (축선 바깥)
            label_radius = max_radius + 40
            label_x = center + label_radius * __import__('math').cos(angle)
            label_y = center + label_radius * __import__('math').sin(angle)

            # 레이블 정렬 조정
            text_anchor = "middle"
            if label_x < center - 5:
                text_anchor = "end"
            elif label_x > center + 5:
                text_anchor = "start"

            stat_label = stat_labels.get(stat_key, stat_key)
            stat_color = stat_colors.get(stat_key, COLOR_PALETTE["primary"])

            lines.append(f'      <text x="{label_x}" y="{label_y}" text-anchor="{text_anchor}" fill="{stat_color}" font-size="14" font-weight="600">{stat_label}</text>')
            lines.append(f'      <text x="{label_x}" y="{label_y + 14}" text-anchor="{text_anchor}" fill="{COLOR_PALETTE["gray_600"]}" font-size="11">({stat_value})</text>')

        # 스탯 폴리곤 (실제 값)
        polygon_points = []
        for i, (stat_key, stat_value) in enumerate(stat_items):
            angle = (angle_step * i - 90) * 3.14159 / 180
            # 값을 0-100 범위로 정규화하여 반지름 계산
            normalized_value = min(100, max(0, stat_value))
            radius = max_radius * (normalized_value / 100)
            point_x = center + radius * __import__('math').cos(angle)
            point_y = center + radius * __import__('math').sin(angle)
            polygon_points.append(f"{point_x},{point_y}")

        # 폴리곤 그리기
        polygon_str = " ".join(polygon_points)
        lines.append(f'      <polygon points="{polygon_str}" fill="{COLOR_PALETTE["primary"]}" fill-opacity="0.3" stroke="{COLOR_PALETTE["primary"]}" stroke-width="2"/>')

        # 스탯 포인트 표시
        for i, (stat_key, stat_value) in enumerate(stat_items):
            angle = (angle_step * i - 90) * 3.14159 / 180
            normalized_value = min(100, max(0, stat_value))
            radius = max_radius * (normalized_value / 100)
            point_x = center + radius * __import__('math').cos(angle)
            point_y = center + radius * __import__('math').sin(angle)

            stat_color = stat_colors.get(stat_key, COLOR_PALETTE["primary"])
            lines.append(f'      <circle cx="{point_x}" cy="{point_y}" r="5" fill="{stat_color}" stroke="white" stroke-width="2"/>')

        lines.append('    </svg>')

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

        lines.append(f'<div class="collapsible-section">')

        # 헤더 (클릭 가능)
        lines.append(f'  <div class="collapsible-header" onclick="toggleSection(\'{section_id}\')" role="button" tabindex="0" aria-expanded="{str(not collapsed).lower()}">')
        lines.append(f'    <div class="collapsible-title-wrapper">')
        lines.append(f'      <span class="collapsible-icon">{icon}</span>')
        lines.append(f'      <h3 class="collapsible-title">{title}</h3>')
        lines.append(f'    </div>')
        lines.append(f'    <span id="{section_id}-arrow" class="collapsible-arrow">{arrow_icon}</span>')
        lines.append(f'  </div>')

        # 내용
        lines.append(f'  <div id="{section_id}-content" class="collapsible-content" style="display: {display_style};">')
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

        lines.append(f'<div class="chart-container">')
        lines.append(f'  <h4 class="chart-title">{title}</h4>')

        # 필터 버튼
        lines.append('  <div class="filter-buttons">')
        lines.append(f'    <button onclick="filterItems(\'all\')" class="filter-btn active" data-filter="all">전체</button>')

        for cat in categories:
            lines.append(f'    <button onclick="filterItems(\'{cat}\')" class="filter-btn" data-filter="{cat}">{cat}</button>')

        lines.append('  </div>')

        # 아이템 리스트
        lines.append('  <div id="items-container">')

        for idx, item in enumerate(items):
            cat = item.get(filter_key, "기타")
            name = item.get(display_key, "")
            desc = item.get(description_key, "")

            lines.append(f'    <div class="list-item" data-category="{cat}">')
            lines.append(f'      <div class="font-bold mb-2" style="color: var(--color-gray-800);">{name}</div>')
            lines.append(f'      <div style="color: var(--color-gray-600); font-size: var(--font-size-sm);">{desc}</div>')
            lines.append(f'      <div class="mt-2" style="color: var(--color-gray-500); font-size: var(--font-size-xs);">카테고리: {cat}</div>')
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

    @staticmethod
    def render_gauge(
        value: float,
        max_value: float = 100,
        title: str = "진행률",
        unit: str = "%",
        color: str = None,
        size: int = 200
    ) -> List[str]:
        """게이지 차트 렌더링 (진행률 시각화).

        Args:
            value: 현재 값
            max_value: 최대 값
            title: 게이지 제목
            unit: 단위
            color: 게이지 색상 (기본값: primary)
            size: 게이지 크기 (픽셀)

        Returns:
            마크다운 라인 리스트
        """
        lines = []

        # 퍼센트 계산
        percentage = min(100, (value / max_value * 100)) if max_value > 0 else 0

        # 색상 결정
        if color is None:
            if percentage >= 80:
                color = COLOR_PALETTE["success"]
            elif percentage >= 50:
                color = COLOR_PALETTE["warning"]
            else:
                color = COLOR_PALETTE["danger"]

        # SVG 게이지
        center = size / 2
        radius = size / 2 - 20
        circumference = 2 * 3.14159 * radius
        offset = circumference - (percentage / 100) * circumference

        lines.append('<div class="chart-container" style="text-align: center;">')
        lines.append(f'  <h4 class="chart-title">{title}</h4>')
        lines.append(f'  <svg width="{size}" height="{size}" viewBox="0 0 {size} {size}">')

        # 배경 원
        lines.append(f'    <circle cx="{center}" cy="{center}" r="{radius}" fill="none" stroke="{COLOR_PALETTE["gray_200"]}" stroke-width="20"/>')

        # 진행 원
        lines.append(f'    <circle cx="{center}" cy="{center}" r="{radius}" fill="none" stroke="{color}" stroke-width="20" stroke-dasharray="{circumference}" stroke-dashoffset="{offset}" stroke-linecap="round" transform="rotate(-90 {center} {center})" style="transition: stroke-dashoffset 0.5s ease;"/>')

        # 중앙 텍스트
        lines.append(f'    <text x="{center}" y="{center - 10}" text-anchor="middle" fill="{COLOR_PALETTE["gray_800"]}" font-size="{size/5}" font-weight="bold">{percentage:.1f}{unit}</text>')
        lines.append(f'    <text x="{center}" y="{center + 20}" text-anchor="middle" fill="{COLOR_PALETTE["gray_600"]}" font-size="{size/10}">{value:.0f} / {max_value:.0f}</text>')

        lines.append('  </svg>')
        lines.append('</div>')
        lines.append("")

        return lines

    @staticmethod
    def render_heatmap(
        data: List[List[int]],
        x_labels: List[str],
        y_labels: List[str],
        title: str = "활동 히트맵",
        cell_size: int = 30
    ) -> List[str]:
        """히트맵 차트 렌더링 (시간/요일별 활동 패턴).

        Args:
            data: 2D 데이터 배열 (행x열)
            x_labels: X축 레이블 (예: 월~일)
            y_labels: Y축 레이블 (예: 00:00~23:00)
            title: 차트 제목
            cell_size: 셀 크기 (픽셀)

        Returns:
            마크다운 라인 리스트
        """
        if not data or not x_labels or not y_labels:
            return []

        lines = []

        # 최대값 찾기 (색상 정규화용)
        max_value = max(max(row) for row in data) if data else 1

        # 차트 크기 계산
        width = len(x_labels) * cell_size + 80
        height = len(y_labels) * cell_size + 80

        lines.append('<div class="chart-container">')
        lines.append(f'  <h4 class="chart-title">{title}</h4>')
        lines.append(f'  <svg width="{width}" height="{height}" viewBox="0 0 {width} {height}">')

        # Y축 레이블
        for i, label in enumerate(y_labels):
            y = 60 + i * cell_size
            lines.append(f'    <text x="60" y="{y + cell_size/2 + 4}" text-anchor="end" fill="{COLOR_PALETTE["gray_600"]}" font-size="11">{label}</text>')

        # X축 레이블
        for i, label in enumerate(x_labels):
            x = 70 + i * cell_size
            lines.append(f'    <text x="{x + cell_size/2}" y="40" text-anchor="middle" fill="{COLOR_PALETTE["gray_600"]}" font-size="11">{label}</text>')

        # 히트맵 셀
        for i, row in enumerate(data):
            for j, value in enumerate(row):
                x = 70 + j * cell_size
                y = 50 + i * cell_size

                # 값에 따른 색상 강도 계산
                intensity = (value / max_value) if max_value > 0 else 0

                # 색상 그라데이션 (연한 파랑 -> 진한 보라)
                if intensity == 0:
                    color = COLOR_PALETTE["gray_100"]
                elif intensity < 0.2:
                    color = "#e0e7ff"
                elif intensity < 0.4:
                    color = "#c7d2fe"
                elif intensity < 0.6:
                    color = "#a5b4fc"
                elif intensity < 0.8:
                    color = "#818cf8"
                else:
                    color = COLOR_PALETTE["primary"]

                lines.append(f'    <rect x="{x}" y="{y}" width="{cell_size-2}" height="{cell_size-2}" fill="{color}" rx="3">')
                lines.append(f'      <title>{y_labels[i]} - {x_labels[j]}: {value}개</title>')
                lines.append('    </rect>')

        lines.append('  </svg>')

        # 범례
        lines.append('  <div style="display: flex; align-items: center; justify-content: center; gap: 8px; margin-top: 16px; font-size: 0.85em; color: ' + COLOR_PALETTE["gray_600"] + ';">')
        lines.append('    <span>적음</span>')
        for intensity_val, color_val in [(0, COLOR_PALETTE["gray_100"]), (0.25, "#c7d2fe"), (0.5, "#a5b4fc"), (0.75, "#818cf8"), (1, COLOR_PALETTE["primary"])]:
            lines.append(f'    <div style="width: 20px; height: 20px; background: {color_val}; border-radius: 3px;"></div>')
        lines.append('    <span>많음</span>')
        lines.append('  </div>')

        lines.append('</div>')
        lines.append("")

        return lines

    @staticmethod
    def render_bubble_chart(
        bubbles: List[Dict[str, Any]],
        title: str = "활동 버블 차트",
        x_label: str = "X축",
        y_label: str = "Y축",
        width: int = 600,
        height: int = 400
    ) -> List[str]:
        """버블 차트 렌더링 (3차원 데이터 시각화).

        Args:
            bubbles: 버블 데이터 [{"x": 10, "y": 20, "size": 30, "label": "A", "color": "#fff"}, ...]
            title: 차트 제목
            x_label: X축 레이블
            y_label: Y축 레이블
            width: 차트 너비
            height: 차트 높이

        Returns:
            마크다운 라인 리스트
        """
        if not bubbles:
            return []

        lines = []

        # 데이터 범위 계산
        x_values = [b.get("x", 0) for b in bubbles]
        y_values = [b.get("y", 0) for b in bubbles]
        size_values = [b.get("size", 1) for b in bubbles]

        x_min, x_max = min(x_values), max(x_values)
        y_min, y_max = min(y_values), max(y_values)
        size_max = max(size_values) if size_values else 1

        # 차트 영역 (여백 포함)
        margin = 60
        chart_width = width - 2 * margin
        chart_height = height - 2 * margin

        lines.append('<div class="chart-container">')
        lines.append(f'  <h4 class="chart-title">{title}</h4>')
        lines.append(f'  <svg width="{width}" height="{height}" viewBox="0 0 {width} {height}">')

        # 축 그리기
        lines.append(f'    <line x1="{margin}" y1="{height - margin}" x2="{width - margin}" y2="{height - margin}" stroke="{COLOR_PALETTE["gray_300"]}" stroke-width="2"/>')
        lines.append(f'    <line x1="{margin}" y1="{margin}" x2="{margin}" y2="{height - margin}" stroke="{COLOR_PALETTE["gray_300"]}" stroke-width="2"/>')

        # 축 레이블
        lines.append(f'    <text x="{width/2}" y="{height - 10}" text-anchor="middle" fill="{COLOR_PALETTE["gray_600"]}" font-size="14">{x_label}</text>')
        lines.append(f'    <text x="20" y="{height/2}" text-anchor="middle" fill="{COLOR_PALETTE["gray_600"]}" font-size="14" transform="rotate(-90 20 {height/2})">{y_label}</text>')

        # 버블 그리기
        for bubble in bubbles:
            x = bubble.get("x", 0)
            y = bubble.get("y", 0)
            size = bubble.get("size", 1)
            label = bubble.get("label", "")
            color = bubble.get("color", COLOR_PALETTE["primary"])

            # 좌표 정규화
            if x_max > x_min:
                norm_x = margin + ((x - x_min) / (x_max - x_min)) * chart_width
            else:
                norm_x = margin + chart_width / 2

            if y_max > y_min:
                norm_y = height - margin - ((y - y_min) / (y_max - y_min)) * chart_height
            else:
                norm_y = height - margin - chart_height / 2

            # 버블 크기 정규화 (5~40 픽셀)
            bubble_radius = 5 + (size / size_max) * 35 if size_max > 0 else 10

            lines.append(f'    <circle cx="{norm_x}" cy="{norm_y}" r="{bubble_radius}" fill="{color}" opacity="0.7" stroke="white" stroke-width="2">')
            lines.append(f'      <title>{label}: X={x}, Y={y}, Size={size}</title>')
            lines.append('    </circle>')

            # 레이블 (작은 버블은 생략)
            if bubble_radius > 15:
                lines.append(f'    <text x="{norm_x}" y="{norm_y + 4}" text-anchor="middle" fill="white" font-size="11" font-weight="bold">{label}</text>')

        lines.append('  </svg>')
        lines.append('</div>')
        lines.append("")

        return lines

    @staticmethod
    def render_network_graph(
        nodes: List[Dict[str, Any]],
        edges: List[Dict[str, Any]],
        title: str = "협업 네트워크",
        width: int = 600,
        height: int = 400
    ) -> List[str]:
        """네트워크 그래프 렌더링 (협업 관계 시각화).

        Args:
            nodes: 노드 데이터 [{"id": "user1", "label": "User 1", "size": 10, "color": "#fff"}, ...]
            edges: 엣지 데이터 [{"from": "user1", "to": "user2", "weight": 5}, ...]
            title: 차트 제목
            width: 차트 너비
            height: 차트 높이

        Returns:
            마크다운 라인 리스트
        """
        if not nodes:
            return []

        lines = []

        # 원형 레이아웃으로 노드 배치
        import math
        center_x = width / 2
        center_y = height / 2
        radius = min(width, height) / 3

        node_positions = {}
        for i, node in enumerate(nodes):
            angle = (2 * math.pi * i) / len(nodes)
            x = center_x + radius * math.cos(angle)
            y = center_y + radius * math.sin(angle)
            node_positions[node["id"]] = (x, y)

        lines.append('<div class="chart-container">')
        lines.append(f'  <h4 class="chart-title">{title}</h4>')
        lines.append(f'  <svg width="{width}" height="{height}" viewBox="0 0 {width} {height}">')

        # 엣지 그리기 (먼저)
        max_weight = max([e.get("weight", 1) for e in edges]) if edges else 1
        for edge in edges:
            from_id = edge.get("from")
            to_id = edge.get("to")
            weight = edge.get("weight", 1)

            if from_id in node_positions and to_id in node_positions:
                x1, y1 = node_positions[from_id]
                x2, y2 = node_positions[to_id]

                # 가중치에 따른 선 두께
                stroke_width = 1 + (weight / max_weight) * 4 if max_weight > 0 else 2
                opacity = 0.3 + (weight / max_weight) * 0.5 if max_weight > 0 else 0.5

                lines.append(f'    <line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{COLOR_PALETTE["gray_400"]}" stroke-width="{stroke_width}" opacity="{opacity}"/>')

        # 노드 그리기
        max_size = max([n.get("size", 1) for n in nodes]) if nodes else 1
        for node in nodes:
            node_id = node["id"]
            x, y = node_positions[node_id]
            label = node.get("label", node_id)
            size = node.get("size", 1)
            color = node.get("color", COLOR_PALETTE["primary"])

            # 노드 크기 정규화
            node_radius = 15 + (size / max_size) * 25 if max_size > 0 else 20

            lines.append(f'    <circle cx="{x}" cy="{y}" r="{node_radius}" fill="{color}" stroke="white" stroke-width="3" opacity="0.9">')
            lines.append(f'      <title>{label}: {size}개 활동</title>')
            lines.append('    </circle>')

            # 레이블
            lines.append(f'    <text x="{x}" y="{y + node_radius + 15}" text-anchor="middle" fill="{COLOR_PALETTE["gray_800"]}" font-size="12" font-weight="bold">{label}</text>')

        lines.append('  </svg>')
        lines.append('</div>')
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
