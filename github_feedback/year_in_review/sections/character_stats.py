"""캐릭터 스탯 섹션 - RPG 스타일 개발자 능력치 시각화."""

from __future__ import annotations

from typing import Any, Dict, List

from ...game_elements import GameRenderer, LevelCalculator


def generate_character_stats(
    year: int,
    total_repos: int,
    total_prs: int,
    total_commits: int,
    repository_analyses: List[Any]
) -> List[str]:
    """게임 캐릭터 스탯 생성 (HTML 버전, 99레벨 시스템 사용)."""
    lines = [
        "## 🎮 개발자 캐릭터 스탯",
        "",
        f"> {year}년 한 해 동안의 활동을 RPG 캐릭터 스탯으로 시각화",
        "",
    ]

    # Calculate overall stats based on activity
    total_activity = total_prs + total_commits

    # 99레벨 시스템으로 레벨 계산
    level, title, rank_emoji = LevelCalculator.calculate_level_99(total_activity)

    # Calculate stats (0-100 scale)
    # 1. Code Quality - based on PR count and diversity
    code_quality = min(100, int(
        (min(total_prs / 80, 1) * 50) +
        (min(total_repos / 15, 1) * 30) +
        0
    ))

    # 2. Productivity - based on commit count
    productivity = min(100, int(
        (min(total_commits / 300, 1) * 60) +
        (min(total_activity / 500, 1) * 40)
    ))

    # 3. Collaboration - based on number of repositories
    collaboration = min(100, int(
        (min(total_repos / 8, 1) * 40) +
        (min(total_prs / 50, 1) * 40) +
        0
    ))

    # 4. Consistency - based on activity distribution
    consistency = min(100, int(
        (min(total_activity / 300, 1) * 50) +
        10
    ))

    # 5. Growth - based on improvement indicators
    repos_with_growth = len([r for r in repository_analyses if r.growth_indicators])
    growth = min(100, int(
        30 +
        (min(repos_with_growth / len(repository_analyses) if repository_analyses else 0, 1) * 70)
    ))

    # 스탯 딕셔너리 구성 (종합 보고서용)
    stats = {
        "code_quality": code_quality,
        "productivity": productivity,
        "collaboration": collaboration,
        "consistency": consistency,
        "growth": growth,
    }

    # 특성 타이틀 결정
    specialty_title = LevelCalculator.get_specialty_title(stats)

    # 경험치 데이터 준비
    experience_data = {
        "🏰 탐험한 던전": total_repos,
        "⚔️  완료한 퀘스트": total_prs,
        "💫 발동한 스킬": total_commits,
        "🎯 총 경험치": f"{total_activity:,} EXP",
    }

    # 뱃지 생성
    badges = LevelCalculator.get_badges_from_stats(
        stats,
        total_commits=total_commits,
        total_prs=total_prs,
        total_repos=total_repos
    )

    # consistency를 꾸준함 뱃지로 교체 (종합 보고서 전용)
    if stats.get("consistency", 0) >= 85:
        badges = [b for b in badges if "협업 챔피언" not in b or b == "🤝 협업 챔피언"]
        badges.append("📅 꾸준함의 화신")

    # GameRenderer로 캐릭터 스탯 렌더링 (HTML 버전)
    # 종합 보고서는 99레벨 시스템 사용 (use_tier_system=False)
    character_lines = GameRenderer.render_character_stats(
        level=level,
        title=title,
        rank_emoji=rank_emoji,
        specialty_title=specialty_title,
        stats=stats,
        experience_data=experience_data,
        badges=badges,
        use_tier_system=False
    )

    lines.extend(character_lines)
    lines.append("---")
    lines.append("")
    return lines


__all__ = ["generate_character_stats"]
