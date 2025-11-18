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
        """게임 스타일 스킬 카드 렌더링.

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

        # 마스터리 바 (20 블록 = 100%)
        filled = mastery_level // 5
        empty = 20 - filled
        mastery_bar = "█" * filled + "░" * empty

        lines.append("```")
        lines.append("╔═══════════════════════════════════════════════════════════╗")

        # 스킬명 - 여러 줄 지원 (40자 제한)
        skill_name_lines = GameRenderer._wrap_text(skill_name, 40)
        padded_skill_name = pad_to_width(skill_name_lines[0], 40, align='left')
        padded_star = pad_to_width(star_display, 5, align='left')
        lines.append(f"║ {skill_emoji} {padded_skill_name} [Lv.{level}] {padded_star} ║")

        # 추가 스킬명 줄 (있을 경우)
        for extra_line in skill_name_lines[1:]:
            padded_extra = pad_to_width(extra_line, 56, align='left')
            lines.append(f"║    {padded_extra} ║")

        lines.append("╠═══════════════════════════════════════════════════════════╣")

        # 스킬 타입
        padded_skill_type = pad_to_width(skill_type, 49, align='left')
        lines.append(f"║ 타입: {type_emoji} {padded_skill_type} ║")

        # 효과 설명 - 여러 줄 지원 (51자 제한)
        effect_lines = GameRenderer._wrap_text(effect_description, 51)
        for i, effect_line in enumerate(effect_lines):
            if i == 0:
                padded_effect = pad_to_width(effect_line, 51, align='left')
                lines.append(f"║ 효과: {padded_effect} ║")
            else:
                padded_effect = pad_to_width(effect_line, 56, align='left')
                lines.append(f"║       {padded_effect} ║")

        lines.append(f"║ 마스터리: [{mastery_bar}] {mastery_level:>3}%  ║")

        if evidence:
            lines.append("╠═══════════════════════════════════════════════════════════╣")
            lines.append("║ 습득 경로:                                                ║")
            for idx, ev in enumerate(evidence[:5], 1):  # 최대 5개로 증가
                # 증거도 여러 줄 지원
                ev_lines = GameRenderer._wrap_text(ev, 54)
                for j, ev_line in enumerate(ev_lines):
                    if j == 0:
                        padded_evidence = pad_to_width(ev_line, 54, align='left')
                        lines.append(f"║   {idx}. {padded_evidence} ║")
                    else:
                        padded_evidence = pad_to_width(ev_line, 56, align='left')
                        lines.append(f"║      {padded_evidence} ║")

        lines.append("╚═══════════════════════════════════════════════════════════╝")
        lines.append("```")
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
        """RPG 스타일 캐릭터 스탯 시각화 렌더링.

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

        lines.append("```")
        lines.append("╔═══════════════════════════════════════════════════════════╗")

        # 타이틀과 레벨, 파워 레벨 표시
        title_padded = pad_to_width(title, 20, align='left')
        if use_tier_system:
            lines.append(f"║  {rank_emoji} Tier {level}: {title_padded} 파워: {int(avg_stat):>3}/100  ║")
        else:
            lines.append(f"║  {rank_emoji} Lv.{level:>2} {title_padded} 파워: {int(avg_stat):>3}/100  ║")

        # 특성 표시
        specialty_padded = pad_to_width(specialty_title, 43, align='left')
        lines.append(f"║  🏅 특성: {specialty_padded} ║")
        lines.append("╠═══════════════════════════════════════════════════════════╣")
        lines.append("║                      능력치 현황                          ║")
        lines.append("╠═══════════════════════════════════════════════════════════╣")

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

        for stat_key, stat_value in stats.items():
            stat_name = stat_names_kr.get(stat_key, stat_key)
            emoji = stat_emojis.get(stat_key, "📊")

            # 시각적 바 생성 (20 블록 = 100%)
            filled = stat_value // 5
            empty = 20 - filled
            bar = "▓" * filled + "░" * empty

            # 스탯명 12 디스플레이 컬럼으로 패딩
            padded_name = pad_to_width(stat_name, 12, align='left')
            lines.append(f"║ {emoji} {padded_name} [{bar}] {stat_value:>3}/100 ║")

        # 경험치 데이터가 있으면 추가
        if experience_data:
            lines.append("╠═══════════════════════════════════════════════════════════╣")
            lines.append("║                      획득 경험치                          ║")
            lines.append("╠═══════════════════════════════════════════════════════════╣")

            for key, value in experience_data.items():
                lines.append(f"║  {key:<20} │  {value:>4}{' ' * 20}║")

        lines.append("╚═══════════════════════════════════════════════════════════╝")
        lines.append("```")
        lines.append("")

        # 뱃지 표시
        if badges:
            lines.append("**🎖️ 획득한 뱃지:**")
            lines.append("")
            for badge in badges:
                lines.append(f"- {badge}")
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
