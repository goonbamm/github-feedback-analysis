"""Character stats section rendering."""

from __future__ import annotations

from typing import List

from ...game_elements import GameRenderer, LevelCalculator
from ..data_loader import StoredReview
from ..stats import ReviewStatsCalculator


def render_character_stats(reviews: List[StoredReview]) -> List[str]:
    """Render RPG-style character stats visualization (티어 시스템 사용)."""
    lines: List[str] = []

    stats = ReviewStatsCalculator.calculate_character_stats(reviews)
    avg_stat = sum(stats.values()) / len(stats) if stats else 0

    # 티어 시스템으로 등급 계산
    tier, title, rank_emoji = LevelCalculator.calculate_tier(avg_stat)

    # 특성 타이틀 결정
    specialty_title = LevelCalculator.get_specialty_title(stats)

    # 뱃지 생성
    total_prs = len(reviews)
    badges = LevelCalculator.get_badges_from_stats(
        stats,
        total_commits=0,  # PR 보고서에는 커밋 수 없음
        total_prs=total_prs,
        total_repos=0,  # PR 보고서에는 저장소 수 없음
    )

    # PR 기반 뱃지 추가
    if total_prs >= 50:
        badges.append("💯 PR 마라토너")
    elif total_prs >= 20:
        badges.append("📝 활발한 기여자")

    # GameRenderer로 캐릭터 스탯 렌더링 (티어 시스템 사용)
    lines.append("## 🎮 개발자 캐릭터 스탯")
    lines.append("")

    # 경험치 데이터 없이 렌더링 (PR 보고서는 경험치 섹션 불필요)
    character_lines = GameRenderer.render_character_stats(
        level=tier,
        title=title,
        rank_emoji=rank_emoji,
        specialty_title=specialty_title,
        stats=stats,
        experience_data={},  # 경험치 데이터 없음
        badges=badges,
        use_tier_system=True,  # 티어 시스템 사용
    )

    lines.extend(character_lines)
    return lines


__all__ = ["render_character_stats"]
