"""커뮤니케이션 스킬 섹션 - 커밋, PR, 리뷰, 이슈 품질 평가."""

from __future__ import annotations

from typing import Any, List, Optional

from ...game_elements import GameRenderer


def generate_communication_skills_section(
    repository_analyses: List[Any]
) -> List[str]:
    """커뮤니케이션 스킬 분석 생성 (HTML 버전)."""
    lines = [
        "## 💬 커뮤니케이션 스킬 트리",
        "",
        "> 커밋, PR, 리뷰, 이슈 등 협업을 위한 커뮤니케이션 능력 평가",
        "",
    ]

    # Aggregate communication skills data across all repositories
    total_commit_quality = []
    total_pr_title_quality = []
    total_review_tone_quality = []
    total_issue_quality = []

    # Aggregate stats
    agg_commit_stats = {"total": 0, "good": 0, "poor": 0}
    agg_pr_stats = {"total": 0, "clear": 0, "unclear": 0}
    agg_review_stats = {"constructive": 0, "harsh": 0, "neutral": 0}
    agg_issue_stats = {"total": 0, "clear": 0, "unclear": 0}

    # Track repositories with data for each skill type
    repos_with_data = 0
    repos_with_commit_data = 0
    repos_with_pr_data = 0
    repos_with_review_data = 0
    repos_with_issue_data = 0

    for repo in repository_analyses:
        has_data = False

        if repo.commit_message_quality is not None:
            total_commit_quality.append(repo.commit_message_quality)
            repos_with_commit_data += 1
            if repo.commit_stats:
                agg_commit_stats["total"] += repo.commit_stats.get("total", 0)
                agg_commit_stats["good"] += repo.commit_stats.get("good", 0)
                agg_commit_stats["poor"] += repo.commit_stats.get("poor", 0)
            has_data = True

        if repo.pr_title_quality is not None:
            total_pr_title_quality.append(repo.pr_title_quality)
            repos_with_pr_data += 1
            if repo.pr_title_stats:
                agg_pr_stats["total"] += repo.pr_title_stats.get("total", 0)
                agg_pr_stats["clear"] += repo.pr_title_stats.get("clear", 0)
                agg_pr_stats["unclear"] += repo.pr_title_stats.get("unclear", 0)
            has_data = True

        if repo.review_tone_quality is not None:
            total_review_tone_quality.append(repo.review_tone_quality)
            repos_with_review_data += 1
            if repo.review_tone_stats:
                agg_review_stats["constructive"] += repo.review_tone_stats.get("constructive", 0)
                agg_review_stats["harsh"] += repo.review_tone_stats.get("harsh", 0)
                agg_review_stats["neutral"] += repo.review_tone_stats.get("neutral", 0)
            has_data = True

        if repo.issue_quality is not None:
            total_issue_quality.append(repo.issue_quality)
            repos_with_issue_data += 1
            if repo.issue_stats:
                agg_issue_stats["total"] += repo.issue_stats.get("total", 0)
                agg_issue_stats["clear"] += repo.issue_stats.get("clear", 0)
                agg_issue_stats["unclear"] += repo.issue_stats.get("unclear", 0)
            has_data = True

        if has_data:
            repos_with_data += 1

    # If no communication skills data, skip this section
    if repos_with_data == 0:
        return []

    # Calculate average quality scores
    avg_commit_quality = sum(total_commit_quality) / len(total_commit_quality) if total_commit_quality else 0
    avg_pr_quality = sum(total_pr_title_quality) / len(total_pr_title_quality) if total_pr_title_quality else 0
    avg_review_quality = sum(total_review_tone_quality) / len(total_review_tone_quality) if total_review_tone_quality else 0
    avg_issue_quality = sum(total_issue_quality) / len(total_issue_quality) if total_issue_quality else 0

    # Build skills table
    headers = ["스킬", "숙련도", "효과", "전체 통계"]
    rows = []

    # Commit message skill
    if total_commit_quality:
        skill_level, skill_name, skill_emoji = _get_skill_level(avg_commit_quality, "커밋")
        mastery_bar = _create_mastery_bar(avg_commit_quality)
        effect = f"전체 커밋의 {int(avg_commit_quality)}%가 명확하고 의미 있는 메시지"
        stats = f"{agg_commit_stats['good']:,}/{agg_commit_stats['total']:,} 커밋 ({repos_with_commit_data}개 저장소)"

        rows.append([
            f'{skill_emoji} <strong>{skill_name}</strong><br><span style="color: #6b7280; font-size: 0.85em;">[{skill_level}]</span>',
            mastery_bar,
            effect,
            stats
        ])

    # PR title skill
    if total_pr_title_quality:
        skill_level, skill_name, skill_emoji = _get_skill_level(avg_pr_quality, "PR")
        mastery_bar = _create_mastery_bar(avg_pr_quality)
        effect = f"전체 PR의 {int(avg_pr_quality)}%가 명확하고 구체적인 제목"
        stats = f"{agg_pr_stats['clear']:,}/{agg_pr_stats['total']:,} PR ({repos_with_pr_data}개 저장소)"

        rows.append([
            f'{skill_emoji} <strong>{skill_name}</strong><br><span style="color: #6b7280; font-size: 0.85em;">[{skill_level}]</span>',
            mastery_bar,
            effect,
            stats
        ])

    # Review tone skill
    if total_review_tone_quality:
        skill_level, skill_name, skill_emoji = _get_skill_level(avg_review_quality, "리뷰")
        mastery_bar = _create_mastery_bar(avg_review_quality)
        total_reviews = agg_review_stats['constructive'] + agg_review_stats['harsh'] + agg_review_stats['neutral']
        effect = f"전체 리뷰의 {int(avg_review_quality)}%가 건설적이고 도움이 되는 톤"
        stats = f"{agg_review_stats['constructive']:,}/{total_reviews:,} 리뷰 ({repos_with_review_data}개 저장소)"

        rows.append([
            f'{skill_emoji} <strong>{skill_name}</strong><br><span style="color: #6b7280; font-size: 0.85em;">[{skill_level}]</span>',
            mastery_bar,
            effect,
            stats
        ])

    # Issue description skill
    if total_issue_quality:
        skill_level, skill_name, skill_emoji = _get_skill_level(avg_issue_quality, "이슈")
        mastery_bar = _create_mastery_bar(avg_issue_quality)
        effect = f"전체 이슈의 {int(avg_issue_quality)}%가 명확하고 재현 가능"
        stats = f"{agg_issue_stats['clear']:,}/{agg_issue_stats['total']:,} 이슈 ({repos_with_issue_data}개 저장소)"

        rows.append([
            f'{skill_emoji} <strong>{skill_name}</strong><br><span style="color: #6b7280; font-size: 0.85em;">[{skill_level}]</span>',
            mastery_bar,
            effect,
            stats
        ])

    # Render table if we have skills
    if rows:
        lines.extend(GameRenderer.render_html_table(
            headers=headers,
            rows=rows,
            title="",
            description="",
            striped=True,
            escape_cells=False
        ))
        lines.append("")

        # Add summary insight
        avg_all_skills = sum([
            avg_commit_quality if total_commit_quality else 0,
            avg_pr_quality if total_pr_title_quality else 0,
            avg_review_quality if total_review_tone_quality else 0,
            avg_issue_quality if total_issue_quality else 0
        ]) / sum([
            1 if total_commit_quality else 0,
            1 if total_pr_title_quality else 0,
            1 if total_review_tone_quality else 0,
            1 if total_issue_quality else 0
        ]) if any([total_commit_quality, total_pr_title_quality, total_review_tone_quality, total_issue_quality]) else 0

        # Determine overall communication level
        if avg_all_skills >= 80:
            overall_level = "💎 **전설급 커뮤니케이터**: 팀에서 모범이 되는 뛰어난 소통 능력을 보유하고 있습니다!"
        elif avg_all_skills >= 60:
            overall_level = "⚔️ **숙련된 협업자**: 효과적으로 의사소통하며 팀 협업에 기여하고 있습니다."
        else:
            overall_level = "🌱 **성장하는 커뮤니케이터**: 더 명확한 의사소통을 위해 노력하고 있습니다. 계속 발전하세요!"

        summary_content = f"""**📊 종합 평가**

전체 평균 커뮤니케이션 점수: **{int(avg_all_skills)}점** / 100점

{overall_level}

**🎯 커뮤니케이션의 중요성**
- 명확한 커밋 메시지는 코드 변경의 의도를 전달합니다
- 구체적인 PR 제목은 리뷰어의 시간을 절약합니다
- 건설적인 리뷰 톤은 팀 분위기와 생산성을 높입니다
- 잘 작성된 이슈는 문제 해결 속도를 향상시킵니다
"""

        lines.extend(GameRenderer.render_info_box(
            title="커뮤니케이션 스킬 종합 평가",
            content=summary_content.strip(),
            emoji="💬",
            bg_color="#f0f9ff",
            border_color="#3b82f6"
        ))

    lines.extend(["---", ""])
    return lines


def _get_skill_level(quality: float, skill_type: str) -> tuple:
    """Get skill level, name, and emoji based on quality score."""
    skill_map = {
        "커밋": {
            "legendary": ("커밋 스토리텔링 마스터", "📜"),
            "expert": ("커밋 메시지 장인", "📝"),
            "learner": ("커밋 작성 견습생", "✍️")
        },
        "PR": {
            "legendary": ("PR 타이틀 아티스트", "🎯"),
            "expert": ("PR 네이밍 전문가", "🔖"),
            "learner": ("PR 제목 학습자", "📌")
        },
        "리뷰": {
            "legendary": ("코드 멘토링 거장", "💬"),
            "expert": ("건설적 리뷰어", "👥"),
            "learner": ("리뷰 커뮤니케이터", "💭")
        },
        "이슈": {
            "legendary": ("이슈 문서화 전문가", "📋"),
            "expert": ("이슈 작성 숙련자", "📝"),
            "learner": ("이슈 보고 학습자", "📄")
        }
    }

    if quality >= 80:
        level = "전설"
        skill_name, emoji = skill_map[skill_type]["legendary"]
    elif quality >= 60:
        level = "숙련"
        skill_name, emoji = skill_map[skill_type]["expert"]
    else:
        level = "수련중"
        skill_name, emoji = skill_map[skill_type]["learner"]

    return level, skill_name, emoji


def _create_mastery_bar(quality: float) -> str:
    """Create HTML mastery bar."""
    color = "#10b981" if quality >= 60 else "#f59e0b" if quality >= 40 else "#ef4444"
    return f'<div style="background: #e5e7eb; border-radius: 4px; height: 20px; width: 150px;"><div style="background: {color}; height: 100%; width: {int(quality)}%; border-radius: 4px; box-shadow: 0 0 10px rgba(16, 185, 129, 0.3);"></div></div><div style="margin-top: 4px; text-align: center; font-size: 0.85em; color: #4b5563;">{int(quality)}%</div>'


__all__ = ["generate_communication_skills_section"]
