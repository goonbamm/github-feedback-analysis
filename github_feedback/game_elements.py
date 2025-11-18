"""게임 요소 렌더링 및 계산 유틸리티.

이 모듈은 모든 보고서에서 사용하는 공통 게임 요소를 제공합니다:
- RPG 스타일 캐릭터 스탯 박스
- 스킬 카드 시스템
- 레벨 및 타이틀 계산
"""
from __future__ import annotations

from typing import Dict, List, Tuple

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
                lines.append(f'        <td style="padding: 6px 0; text-align: right; font-weight: bold; color: #fbbf24;">{value:,}</td>')
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


__all__ = ["GameRenderer", "LevelCalculator"]
