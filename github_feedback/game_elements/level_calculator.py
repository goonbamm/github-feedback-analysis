"""레벨 및 타이틀 계산 유틸리티."""
from __future__ import annotations

from typing import Dict, List, Tuple


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


__all__ = ["LevelCalculator"]
