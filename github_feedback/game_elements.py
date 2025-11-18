"""게임 요소 렌더링 및 계산 유틸리티.

이 모듈은 모든 보고서에서 사용하는 공통 게임 요소를 제공합니다:
- RPG 스타일 캐릭터 스탯 박스
- 스킬 카드 시스템
- 레벨 및 타이틀 계산
"""
from __future__ import annotations

from typing import Any, Dict, List, Tuple

from .utils import pad_to_width


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

        # 마스터리 바
        lines.append(f'  <div style="margin-bottom: 12px;">')
        lines.append(f'    <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">')
        lines.append(f'      <span style="font-weight: bold;">마스터리</span>')
        lines.append(f'      <span style="font-weight: bold;">{mastery_percentage}%</span>')
        lines.append(f'    </div>')
        lines.append(f'    <div style="background: rgba(0,0,0,0.3); border-radius: 10px; height: 20px; overflow: hidden;">')
        lines.append(f'      <div style="background: linear-gradient(90deg, #4ade80 0%, #22c55e 100%); height: 100%; width: {bar_filled_width}%; transition: width 0.3s ease;"></div>')
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
            "growth": "📈",
        }

        stat_names_kr = {
            "code_quality": "코드 품질",
            "collaboration": "협업력",
            "problem_solving": "문제 해결력",
            "productivity": "생산성",
            "growth": "성장성",
        }

        # 스탯 색상 정의
        stat_colors = {
            "code_quality": "#3b82f6",  # 파란색
            "collaboration": "#8b5cf6",  # 보라색
            "problem_solving": "#ec4899",  # 핑크색
            "productivity": "#f59e0b",  # 주황색
            "growth": "#10b981",  # 초록색
        }

        for stat_key, stat_value in stats.items():
            stat_name = stat_names_kr.get(stat_key, stat_key)
            emoji = stat_emojis.get(stat_key, "📊")
            color = stat_colors.get(stat_key, "#6b7280")

            lines.append(f'    <div style="margin-bottom: 12px;">')
            lines.append(f'      <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">')
            lines.append(f'        <span style="font-weight: bold;">{emoji} {stat_name}</span>')
            lines.append(f'        <span style="font-weight: bold; color: {color};">{stat_value}/100</span>')
            lines.append(f'      </div>')
            lines.append(f'      <div style="background: rgba(255,255,255,0.1); border-radius: 10px; height: 16px; overflow: hidden;">')
            lines.append(f'        <div style="background: {color}; height: 100%; width: {stat_value}%; transition: width 0.3s ease;"></div>')
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
        striped: bool = True
    ) -> List[str]:
        """범용 HTML 테이블 렌더링.

        Args:
            headers: 테이블 헤더 리스트
            rows: 테이블 행 데이터 (각 행은 문자열 리스트)
            title: 테이블 제목 (선택)
            description: 테이블 설명 (선택)
            striped: 줄무늬 스타일 적용 여부

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
                lines.append(f'        <td style="padding: 10px; color: #2d3748;">{cell}</td>')
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


class LevelCalculator:
    """레벨 및 타이틀 계산 유틸리티."""

    # 종합 보고서용 99레벨 시스템
    LEVEL_99_TITLES = [
        (500, 99, "전설의 코드마스터", "👑"),
        (300, 80, "그랜드마스터", "💎"),
        (150, 60, "마스터", "🏆"),
        (75, 40, "전문가", "⭐"),
        (30, 20, "숙련자", "💫"),
        (10, 10, "초보자", "🌱"),
        (0, 1, "견습생", "✨"),
    ]

    # 개별/일반 보고서용 티어 시스템
    TIER_SYSTEM = [
        (90, 6, "그랜드마스터", "👑"),
        (75, 5, "마스터", "🏆"),
        (60, 4, "전문가", "⭐"),
        (40, 3, "숙련자", "💎"),
        (20, 2, "견습생", "🎓"),
        (0, 1, "초보자", "🌱"),
    ]

    # 특성 타이틀 매핑
    SPECIALTY_TITLES = {
        "코드 품질": "코드 아키텍트",
        "협업력": "팀 플레이어",
        "문제 해결력": "문제 해결사",
        "생산성": "스피드 러너",
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
                if threshold == 500:
                    level = 99
                elif threshold == 300:
                    level = min(99, 80 + (total_activity - 300) // 20)
                elif threshold == 150:
                    level = min(99, 60 + (total_activity - 150) // 10)
                elif threshold == 75:
                    level = min(99, 40 + (total_activity - 75) // 5)
                elif threshold == 30:
                    level = min(99, 20 + (total_activity - 30) // 3)
                elif threshold == 10:
                    level = min(99, 10 + (total_activity - 10) // 2)
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

        # 스탯 기반 뱃지 (80 이상)
        if stats.get("code_quality", 0) >= 80:
            badges.append("🏅 코드 마스터")
        if stats.get("collaboration", 0) >= 80:
            badges.append("🤝 협업 챔피언")
        if stats.get("problem_solving", 0) >= 80:
            badges.append("🧠 문제 해결 전문가")
        if stats.get("productivity", 0) >= 80:
            badges.append("⚡ 생산성 괴물")
        if stats.get("growth", 0) >= 80:
            badges.append("🚀 급성장 개발자")

        # 활동량 기반 뱃지
        if total_commits >= 200:
            badges.append("💯 커밋 마라토너")
        elif total_commits >= 100:
            badges.append("📝 활발한 커미터")

        if total_prs >= 50:
            badges.append("🔀 PR 마스터")
        elif total_prs >= 20:
            badges.append("🔄 PR 컨트리뷰터")

        if total_repos >= 10:
            badges.append("🌐 멀티버스 탐험가")
        elif total_repos >= 5:
            badges.append("🗺️ 던전 크롤러")

        return badges


class EquipmentSystem:
    """게임 테마 장비 시스템 - 기술 스택을 RPG 장비로 변환."""

    # 언어/기술별 장비 매핑 (이름, 카테고리, 설명)
    TECH_EQUIPMENT = {
        # Programming Languages
        "Python": {
            "legendary": ("🐍 전설의 파이썬 스태프", "지팡이", "데이터의 마법사를 위한 만능 지팡이"),
            "rare": ("🔮 파이썬 크리스탈", "마법석", "머신러닝과 자동화의 힘"),
            "common": ("📜 파이썬 스크롤", "주문서", "스크립팅의 기본 무기"),
        },
        "JavaScript": {
            "legendary": ("⚡ 자바스크립트 듀얼블레이드", "쌍검", "프론트엔드와 백엔드를 동시에 제압"),
            "rare": ("🌐 이벤트루프 샤크람", "차크람", "비동기 공격의 대가"),
            "common": ("📱 웹 단검", "단검", "빠르고 가벼운 웹 개발"),
        },
        "TypeScript": {
            "legendary": ("🛡️ 타입가디언 성검", "성검", "타입 안정성을 수호하는 전설의 검"),
            "rare": ("⚔️ 타입체커 그레이트소드", "대검", "컴파일 타임의 수호자"),
            "common": ("🔰 타입 세이프티 소드", "검", "안전한 코드의 시작"),
        },
        "Java": {
            "legendary": ("☕ 엔터프라이즈 엑스칼리버", "성검", "대규모 시스템을 다스리는 왕의 검"),
            "rare": ("🏛️ OOP 템플 실드", "방패", "객체지향의 견고한 방어"),
            "common": ("📦 자바 클래스 해머", "해머", "묵직하고 강력한 개발"),
        },
        "C++": {
            "legendary": ("⚙️ 메모리마스터 배틀액스", "전투도끼", "저수준 제어의 극한"),
            "rare": ("🔧 포인터 워해머", "전투해머", "메모리를 직접 다루는 힘"),
            "common": ("🛠️ 컴파일러 톱날", "톱날", "성능 최적화의 시작"),
        },
        "C#": {
            "legendary": ("💎 닷넷 크라운", "왕관", "마이크로소프트 왕국의 보물"),
            "rare": ("🎯 유니티 매직스태프", "지팡이", "게임 세계를 창조하는 힘"),
            "common": ("🔷 C# 크리스탈 소드", "검", "윈도우 개발의 기본"),
        },
        "Go": {
            "legendary": ("🚀 고퍼 로켓런처", "발사기", "동시성의 폭발적인 힘"),
            "rare": ("⚡ 고루틴 쇄도검", "검", "병렬처리의 예술"),
            "common": ("🔄 채널 신호기", "신호기", "간결한 동시성"),
        },
        "Rust": {
            "legendary": ("🦀 메모리안전 신성갑옷", "갑옷", "제로코스트로 완벽한 방어"),
            "rare": ("⚔️ 소유권 미스릴검", "검", "컴파일 타임 보장의 힘"),
            "common": ("🔐 보로우체커 실드", "방패", "안전한 메모리 관리"),
        },
        "Ruby": {
            "legendary": ("💎 레일즈 루비 티아라", "왕관", "개발자 행복의 정수"),
            "rare": ("🎨 엘레강트 루비링", "반지", "우아한 코드의 상징"),
            "common": ("✨ 루비 젬", "보석", "빠른 프로토타이핑"),
        },
        "Swift": {
            "legendary": ("🦅 스위프트윙 활", "활", "iOS 왕국을 지배하는 명궁"),
            "rare": ("📱 애플 실버애로우", "화살", "모바일 개발의 날카로움"),
            "common": ("🎯 스위프트 석궁", "석궁", "애플 생태계의 무기"),
        },
        "Kotlin": {
            "legendary": ("🎯 코틀린 드래곤블레이드", "용검", "안드로이드의 새로운 전설"),
            "rare": ("⚡ 코루틴 라이트닝스피어", "창", "비동기의 번개"),
            "common": ("📱 모던 안드로이드 소드", "검", "자바의 진화형"),
        },
        "PHP": {
            "legendary": ("🐘 라라벨 엘리펀트 로드", "지팡이", "웹 개발의 거대한 힘"),
            "rare": ("🌐 워드프레스 완드", "완드", "웹의 30%를 지배"),
            "common": ("📄 서버사이드 스크립트", "두루마리", "동적 웹의 기본"),
        },
        "R": {
            "legendary": ("📊 통계마법진", "마법진", "데이터 과학의 비밀병기"),
            "rare": ("📈 분석 크리스탈볼", "수정구", "통계적 통찰력"),
            "common": ("🔬 데이터 렌즈", "렌즈", "과학적 분석"),
        },
        "Scala": {
            "legendary": ("⚖️ 함수형 저울검", "검", "객체지향과 함수형의 완벽한 균형"),
            "rare": ("🎭 스칼라 듀얼마스크", "마스크", "두 세계의 대가"),
            "common": ("🔷 JVM 크리스탈", "보석", "자바 생태계의 진화"),
        },
        "Dart": {
            "legendary": ("🎯 플러터 신의화살", "신궁", "크로스플랫폼 제패"),
            "rare": ("💙 플러터윙 다트", "투척무기", "아름다운 UI의 예술"),
            "common": ("📱 모바일 다트건", "총", "빠른 개발 도구"),
        },

        # Frontend/Markup
        "HTML": {
            "legendary": ("📐 시맨틱 아키텍처 블루프린트", "설계도", "웹의 기반 구조"),
            "rare": ("🏗️ HTML5 건축도구", "도구", "모던 웹 구조"),
            "common": ("📄 웹페이지 템플릿", "템플릿", "웹의 뼈대"),
        },
        "CSS": {
            "legendary": ("🎨 플렉스박스 마법붓", "마법붓", "레이아웃의 예술가"),
            "rare": ("✨ 애니메이션 팔레트", "팔레트", "시각적 마법"),
            "common": ("🖌️ 스타일링 붓", "붓", "디자인의 기본"),
        },
        "SCSS": {
            "legendary": ("🎭 믹스인 마스터 팔레트", "팔레트", "스타일의 재사용 마법"),
            "rare": ("🔮 변수 크리스탈", "수정", "동적 스타일링"),
            "common": ("🎨 SASS 붓", "붓", "CSS의 진화"),
        },

        # Frameworks/Libraries
        "React": {
            "legendary": ("⚛️ 리액트 네뷸라 건틀렛", "건틀렛", "컴포넌트 우주를 지배"),
            "rare": ("🔄 훅스 에너지링", "반지", "함수형 UI의 힘"),
            "common": ("📦 컴포넌트 박스", "상자", "재사용 가능한 UI"),
        },
        "Vue": {
            "legendary": ("💚 뷰 에메랄드 스태프", "지팡이", "반응성 마법의 정수"),
            "rare": ("🔮 리액티브 크리스탈", "수정", "양방향 바인딩"),
            "common": ("✨ 뷰 컴포넌트 젬", "보석", "점진적 프레임워크"),
        },
        "Angular": {
            "legendary": ("🅰️ 앵귤러 엔터프라이즈 아머", "갑옷", "대규모 앱의 철벽방어"),
            "rare": ("🔴 타입스크립트 실드", "방패", "강력한 구조"),
            "common": ("🏗️ 앵귤러 프레임", "프레임", "완전한 프레임워크"),
        },
        "Django": {
            "legendary": ("🎸 장고 마에스트로 기타", "악기", "웹 프레임워크의 명인"),
            "rare": ("🔐 ORM 보안갑옷", "갑옷", "데이터베이스 마법"),
            "common": ("🌐 웹 프레임워크 툴킷", "도구", "풀스택 개발"),
        },
        "Flask": {
            "legendary": ("🧪 플라스크 연금술 세트", "연금술", "마이크로서비스의 정수"),
            "rare": ("⚗️ 미니멀 엘릭서", "물약", "가볍고 강력한 마법"),
            "common": ("🔬 마이크로 프레임워크", "도구", "작지만 강력함"),
        },
        "Spring": {
            "legendary": ("🌱 스프링 라이프트리", "세계수", "엔터프라이즈 생태계"),
            "rare": ("☘️ 의존성주입 오브", "구슬", "IoC의 힘"),
            "common": ("🍃 스프링 부트 씨앗", "씨앗", "빠른 시작"),
        },
        "Express": {
            "legendary": ("🚂 익스프레스 고속열차", "열차", "Node.js의 초고속 배송"),
            "rare": ("⚡ 미들웨어 체인", "사슬", "확장 가능한 아키텍처"),
            "common": ("📦 노드 서버 박스", "상자", "간단한 백엔드"),
        },
        "Next.js": {
            "legendary": ("▲ 넥스트 차원문", "포탈", "서버/클라이언트 경계를 넘어"),
            "rare": ("🚀 SSR 로켓", "로켓", "서버사이드 렌더링"),
            "common": ("⚡ 리액트 부스터", "부스터", "향상된 리액트"),
        },

        # Databases
        "SQL": {
            "legendary": ("🗄️ 관계형 크리스탈 라이브러리", "도서관", "데이터의 완벽한 조직"),
            "rare": ("📊 쿼리 마법서", "마법서", "데이터 조작의 언어"),
            "common": ("🔍 데이터 검색도구", "도구", "정보 관리"),
        },
        "PostgreSQL": {
            "legendary": ("🐘 포스트그레스 엔사이클로피디아", "백과사전", "가장 진보한 오픈소스 DB"),
            "rare": ("📚 ACID 스크롤", "두루마리", "트랜잭션의 보장"),
            "common": ("🗃️ 관계형 DB 상자", "상자", "안정적인 저장소"),
        },
        "MySQL": {
            "legendary": ("🐬 마이SQL 오션 트라이던트", "삼지창", "웹의 바다를 지배"),
            "rare": ("💧 데이터 스트림 스태프", "지팡이", "흐르는 데이터"),
            "common": ("🗄️ RDBMS 저장고", "저장고", "널리 쓰이는 DB"),
        },
        "MongoDB": {
            "legendary": ("🍃 몽고DB 리프 컬렉션", "컬렉션", "문서 지향의 자유"),
            "rare": ("📄 도큐먼트 그리모어", "마법서", "유연한 스키마"),
            "common": ("🗂️ NoSQL 카드덱", "카드", "비정형 데이터"),
        },
        "Redis": {
            "legendary": ("⚡ 레디스 라이트닝 캐시", "번개", "초고속 인메모리 저장"),
            "rare": ("💨 스피드 메모리 링", "반지", "극한의 속도"),
            "common": ("🔥 캐시 부스터", "부스터", "성능 향상"),
        },

        # Tools & Config
        "Docker": {
            "legendary": ("🐳 도커 차원 컨테이너", "차원주머니", "어디서나 동일한 환경"),
            "rare": ("📦 이미지 캡슐", "캡슐", "격리된 세계"),
            "common": ("🏗️ 컨테이너 박스", "상자", "환경 일관성"),
        },
        "Kubernetes": {
            "legendary": ("☸️ 쿠버네티스 오케스트라 지휘봉", "지휘봉", "컨테이너 오케스트라의 마에스트로"),
            "rare": ("🎼 클러스터 악보", "악보", "자동화된 배포"),
            "common": ("⚙️ 오케스트레이션 도구", "도구", "컨테이너 관리"),
        },
        "Git": {
            "legendary": ("🌳 깃 타임트리", "세계수", "시간을 넘나드는 버전관리"),
            "rare": ("⏰ 커밋 타임워치", "시계", "변경사항 추적"),
            "common": ("📝 버전컨트롤 노트", "노트", "협업의 기본"),
        },
        "GitHub": {
            "legendary": ("🐙 옥토캣 레전더리 클로크", "망토", "오픈소스의 중심"),
            "rare": ("⭐ 스타 컬렉터 뱃지", "뱃지", "협업 플랫폼"),
            "common": ("🔀 PR 포털", "포탈", "코드 공유"),
        },
        "YAML": {
            "legendary": ("📜 설정 마스터 스크롤", "두루마리", "완벽한 구성 마법"),
            "rare": ("⚙️ 컨피그 크리스탈", "수정", "설정의 예술"),
            "common": ("📄 설정 파일", "파일", "간단한 설정"),
        },
        "JSON": {
            "legendary": ("💎 데이터 다이아몬드", "다이아몬드", "구조화된 정보의 보석"),
            "rare": ("📊 파싱 크리스탈", "수정", "데이터 교환"),
            "common": ("📋 JSON 카드", "카드", "데이터 포맷"),
        },
        "Markdown": {
            "legendary": ("✍️ 마크다운 신성한 깃펜", "깃펜", "문서화의 예술가"),
            "rare": ("📝 포맷팅 스타일러스", "펜", "아름다운 문서"),
            "common": ("📄 문서 템플릿", "템플릿", "간단한 작성"),
        },

        # Testing & Quality
        "Jest": {
            "legendary": ("🃏 제스트 조커 카드덱", "카드덱", "테스트의 만능 도구"),
            "rare": ("🎭 목 마스크", "가면", "격리된 테스트"),
            "common": ("✅ 유닛테스트 체크리스트", "체크리스트", "테스트 자동화"),
        },
        "Pytest": {
            "legendary": ("🧪 파이테스트 연금술 세트", "연금술", "파이썬 테스트의 현자의 돌"),
            "rare": ("🔬 픽스처 마법진", "마법진", "테스트 환경 구성"),
            "common": ("✅ 테스트 체커", "체커", "품질 보증"),
        },

        # Cloud & DevOps
        "AWS": {
            "legendary": ("☁️ 아마존 클라우드 왕국", "왕국", "무한한 클라우드 제국"),
            "rare": ("⚡ EC2 파워젬", "보석", "확장 가능한 컴퓨팅"),
            "common": ("📦 클라우드 박스", "상자", "클라우드 서비스"),
        },
        "Azure": {
            "legendary": ("💠 애저 스카이 크라운", "왕관", "마이크로소프트 클라우드 제국"),
            "rare": ("🔷 클라우드 크리스탈", "수정", "엔터프라이즈 클라우드"),
            "common": ("☁️ 애저 클라우드", "구름", "클라우드 플랫폼"),
        },
        "GCP": {
            "legendary": ("🌐 구글 클라우드 글로브", "지구본", "구글의 인프라"),
            "rare": ("⚡ 컴퓨트 엔진", "엔진", "강력한 컴퓨팅"),
            "common": ("☁️ GCP 서비스", "서비스", "클라우드 도구"),
        },

        # Mobile
        "Android": {
            "legendary": ("🤖 안드로이드 전투로봇", "로봇", "모바일 생태계 지배"),
            "rare": ("📱 그린로봇 건틀렛", "건틀렛", "다양한 기기 제어"),
            "common": ("🔧 안드로이드 툴킷", "도구", "모바일 개발"),
        },
        "iOS": {
            "legendary": ("🍎 아이폰 골든애플", "황금사과", "프리미엄 모바일 경험"),
            "rare": ("📱 애플 에코시스템 링", "반지", "통합된 생태계"),
            "common": ("🔨 iOS 개발도구", "도구", "애플 개발"),
        },

        # AI/ML
        "TensorFlow": {
            "legendary": ("🧠 텐서플로우 뉴럴네트워크 왕관", "왕관", "딥러닝의 제왕"),
            "rare": ("🔮 AI 매트릭스 크리스탈", "수정", "기계학습의 힘"),
            "common": ("🤖 ML 모델", "모델", "인공지능 기초"),
        },
        "PyTorch": {
            "legendary": ("🔥 파이토치 플레임 세프터", "홀", "동적 신경망의 화염"),
            "rare": ("⚡ 텐서 라이트닝", "번개", "유연한 딥러닝"),
            "common": ("🧮 뉴럴 네트워크", "네트워크", "연구용 ML"),
        },
    }

    # 기본 템플릿 (매핑되지 않은 기술용)
    DEFAULT_EQUIPMENT = {
        "legendary": ("🌟 전설의 {tech} 아티팩트", "아티팩트", "희귀하고 강력한 {tech} 도구"),
        "rare": ("✨ {tech} 마스터 도구", "도구", "{tech} 전문가의 무기"),
        "common": ("🔧 {tech} 기본 장비", "장비", "{tech} 개발 도구"),
    }

    # 장비 등급별 기준
    EQUIPMENT_TIERS = [
        (30.0, "legendary", "⭐⭐⭐", "#fbbf24", "전설"),  # Gold
        (15.0, "rare", "⭐⭐", "#8b5cf6", "희귀"),         # Purple
        (5.0, "common", "⭐", "#3b82f6", "일반"),          # Blue
        (0.0, "basic", "", "#6b7280", "보조"),            # Gray
    ]

    @staticmethod
    def get_equipment_info(tech_name: str, usage_percentage: float) -> dict:
        """기술명과 사용률을 기반으로 장비 정보 반환.

        Args:
            tech_name: 기술/언어 이름
            usage_percentage: 사용 비율 (0-100)

        Returns:
            장비 정보 딕셔너리 {
                "name": 장비 이름,
                "category": 장비 카테고리,
                "description": 설명,
                "tier": 등급,
                "tier_stars": 별 표시,
                "tier_color": 색상,
                "tier_name": 등급명,
                "emoji": 이모지
            }
        """
        # 등급 결정
        tier_info = None
        for threshold, tier, stars, color, tier_name in EquipmentSystem.EQUIPMENT_TIERS:
            if usage_percentage >= threshold:
                tier_info = (tier, stars, color, tier_name)
                break

        if not tier_info:
            tier_info = ("basic", "", "#6b7280", "보조")

        tier, stars, color, tier_name = tier_info

        # 장비 정보 가져오기
        tech_equipment = EquipmentSystem.TECH_EQUIPMENT.get(tech_name)

        if tech_equipment and tier in tech_equipment:
            name, category, description = tech_equipment[tier]
        elif tech_equipment and "legendary" in tech_equipment:
            # 전설 장비가 있지만 등급이 낮으면 기본 템플릿 사용
            default = EquipmentSystem.DEFAULT_EQUIPMENT.get(tier, EquipmentSystem.DEFAULT_EQUIPMENT["common"])
            name, category, description = (
                default[0].format(tech=tech_name),
                default[1],
                default[2].format(tech=tech_name)
            )
        else:
            # 매핑되지 않은 기술은 기본 템플릿 사용
            default = EquipmentSystem.DEFAULT_EQUIPMENT.get(tier, EquipmentSystem.DEFAULT_EQUIPMENT["common"])
            name, category, description = (
                default[0].format(tech=tech_name),
                default[1],
                default[2].format(tech=tech_name)
            )

        # 이모지 추출 (이름 앞부분에서)
        emoji = ""
        if name and len(name) > 0:
            # 첫 번째 문자가 이모지인지 확인
            first_char = name[0]
            if ord(first_char) > 127:  # Non-ASCII (이모지 포함)
                emoji = first_char

        return {
            "name": name,
            "category": category,
            "description": description,
            "tier": tier,
            "tier_stars": stars,
            "tier_color": color,
            "tier_name": tier_name,
            "emoji": emoji,
        }

    @staticmethod
    def render_equipment_card(
        rank: int,
        tech_name: str,
        equipment_info: dict,
        usage_count: int,
        usage_percentage: float
    ) -> str:
        """장비 카드를 HTML로 렌더링.

        Args:
            rank: 순위
            tech_name: 기술명
            equipment_info: get_equipment_info에서 반환된 정보
            usage_count: 사용 횟수
            usage_percentage: 사용 비율

        Returns:
            HTML 문자열
        """
        tier_color = equipment_info["tier_color"]

        # 등급별 배경 그라디언트
        gradients = {
            "legendary": "linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%)",
            "rare": "linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%)",
            "common": "linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)",
            "basic": "linear-gradient(135deg, #6b7280 0%, #4b5563 100%)",
        }
        bg_gradient = gradients.get(equipment_info["tier"], gradients["basic"])

        html = f'''
<div style="border: 3px solid {tier_color}; border-radius: 12px; padding: 16px; margin: 12px 0; background: {bg_gradient}; color: white; box-shadow: 0 4px 8px rgba(0,0,0,0.2); font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;">
    <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 12px;">
        <div style="flex: 1;">
            <div style="font-size: 0.85em; opacity: 0.9; margin-bottom: 4px;">
                #{rank} · {equipment_info["tier_name"]} {equipment_info["tier_stars"]}
            </div>
            <div style="font-size: 1.3em; font-weight: bold; margin-bottom: 4px; line-height: 1.3;">
                {equipment_info["name"]}
            </div>
            <div style="background: rgba(0,0,0,0.3); display: inline-block; padding: 4px 8px; border-radius: 4px; font-size: 0.85em; margin-bottom: 8px;">
                📦 {equipment_info["category"]}
            </div>
        </div>
        <div style="text-align: right; min-width: 80px;">
            <div style="font-size: 2em; margin-bottom: 4px;">{equipment_info["emoji"]}</div>
            <div style="background: rgba(0,0,0,0.4); padding: 4px 8px; border-radius: 8px; font-size: 0.9em; font-weight: bold;">
                {usage_percentage:.1f}%
            </div>
        </div>
    </div>

    <div style="background: rgba(0,0,0,0.2); padding: 10px; border-radius: 6px; margin-bottom: 12px;">
        <div style="font-size: 0.9em; opacity: 0.95; line-height: 1.4;">
            💬 {equipment_info["description"]}
        </div>
    </div>

    <div style="display: flex; justify-content: space-between; align-items: center;">
        <div style="flex: 1; margin-right: 12px;">
            <div style="background: rgba(0,0,0,0.3); border-radius: 10px; height: 24px; overflow: hidden;">
                <div style="background: rgba(255,255,255,0.9); height: 100%; width: {min(usage_percentage, 100)}%; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 0.75em; font-weight: bold; color: #1f2937; transition: width 0.3s ease;">
                    {usage_percentage:.1f}%
                </div>
            </div>
        </div>
        <div style="text-align: right; font-size: 0.9em; opacity: 0.9;">
            ⚡ {usage_count:,}회 사용
        </div>
    </div>
</div>
'''
        return html.strip()


__all__ = ["GameRenderer", "LevelCalculator", "EquipmentSystem"]
