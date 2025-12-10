"""최고 업적 섹션 - 한 해 동안의 주요 성과 요약."""

from __future__ import annotations

from typing import Any, Dict, List

from ...game_elements import GameRenderer


def generate_executive_summary(
    repository_analyses: List[Any], tech_stack: List[tuple]
) -> List[str]:
    """게임 스타일 최고 업적 섹션 생성 (HTML 버전)."""
    lines = [
        "## 🏆 전설의 업적",
        "",
        "> 한 해 동안 달성한 최고의 기록들",
        "",
    ]

    # Most active repository
    most_active = max(repository_analyses, key=lambda r: r.pr_count)
    most_commits = max(repository_analyses, key=lambda r: r.year_commits)

    # Build achievements list
    achievement_text = f"🥇 **최다 활동 던전**: {most_active.full_name}\n   └─ 완료 퀘스트: {most_active.pr_count}개"

    if most_commits.full_name != most_active.full_name:
        achievement_text += f"\n\n🥈 **최다 커밋 던전**: {most_commits.full_name}\n   └─ 커밋 횟수: {most_commits.year_commits}회"

    if tech_stack:
        top_3_tech = [tech[0] for tech in tech_stack[:3]]
        tech_str = ', '.join(top_3_tech)
        achievement_text += f"\n\n💻 **주력 무기(기술)**: {tech_str}"

    # Render as info box
    lines.extend(GameRenderer.render_info_box(
        title="🎖️ 최고 업적 🎖️",
        content=achievement_text,
        emoji="🏆",
        bg_color="#fef3c7",
        border_color="#fbbf24"
    ))

    lines.extend(["---", ""])
    return lines


__all__ = ["generate_executive_summary"]
