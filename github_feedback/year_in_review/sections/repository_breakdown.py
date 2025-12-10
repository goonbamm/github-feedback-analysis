"""저장소별 상세 분석 섹션 - 각 저장소의 활동 및 성장 지표."""

from __future__ import annotations

from pathlib import Path
from typing import Any, List

from ...game_elements import GameRenderer


def generate_repository_breakdown(
    repository_analyses: List[Any], output_dir: Path
) -> List[str]:
    """던전별 탐험 기록 생성."""
    lines = [
        "## 🏰 던전 탐험 기록",
        "",
        "> 각 저장소 던전에서의 모험을 상세히 기록합니다",
        "",
    ]

    for idx, repo in enumerate(repository_analyses, 1):
        # Calculate dungeon difficulty based on activity
        total_activity = repo.pr_count + repo.year_commits
        difficulty, difficulty_emoji = _calculate_difficulty(total_activity)

        lines.append(f"### {idx}. {difficulty_emoji} {repo.full_name}")
        lines.append("")
        lines.append(f"**난이도**: {difficulty}")
        lines.append("")

        # Build stats content
        stats_content = _build_stats_content(repo)

        # Render as info box
        lines.extend(GameRenderer.render_info_box(
            title="던전 클리어 통계",
            content=stats_content,
            emoji="📊",
            bg_color="#eff6ff",
            border_color="#3b82f6"
        ))

        # Link to detailed report
        if repo.integrated_report_path:
            rel_from_reports = repo.integrated_report_path.relative_to(output_dir.parent)
            rel_from_year_in_review = Path("..") / rel_from_reports
            lines.append(f"📜 **[상세 보고서 보기]({rel_from_year_in_review})**")
            lines.append("")

        # Render strengths table
        if repo.strengths:
            lines.extend(_render_strengths_table(repo.strengths))

        # Render improvements table
        if repo.improvements:
            lines.extend(_render_improvements_table(repo.improvements))

        # Render growth indicators table
        if repo.growth_indicators:
            lines.extend(_render_growth_indicators_table(repo.growth_indicators))

        lines.append("---")
        lines.append("")

    return lines


def _calculate_difficulty(total_activity: int) -> tuple[str, str]:
    """Calculate dungeon difficulty based on activity."""
    if total_activity >= 100:
        return "⭐⭐⭐⭐⭐ (전설)", "💎"
    elif total_activity >= 50:
        return "⭐⭐⭐⭐ (어려움)", "🔥"
    elif total_activity >= 20:
        return "⭐⭐⭐ (보통)", "⚔️"
    elif total_activity >= 10:
        return "⭐⭐ (쉬움)", "🌟"
    else:
        return "⭐ (입문)", "✨"


def _build_stats_content(repo: Any) -> str:
    """Build stats content for repository."""
    stats_content = f"⚔️  **완료한 퀘스트 (PR)**: {repo.pr_count}개\n"
    stats_content += f"💫 **발동한 스킬 (커밋)**: {repo.year_commits}회 (올해)\n"
    stats_content += f"📊 **총 기여 횟수**: {repo.commit_count}회 (전체)"

    if repo.tech_stack:
        top_langs = sorted(repo.tech_stack.items(), key=lambda x: x[1], reverse=True)[:3]
        stats_content += "\n\n🔧 **사용한 주요 기술**:"
        for lang, count in top_langs:
            stats_content += f"\n   • {lang}: {count}회"

    return stats_content


def _render_strengths_table(strengths: List[Any]) -> List[str]:
    """Render strengths table."""
    lines = [
        "#### ✨ 획득한 스킬",
        "",
    ]

    # Build table data
    headers = ["스킬", "설명", "영향도", "증거"]
    rows = []

    for strength in strengths[:5]:
        category = strength.get("category", "")
        desc = strength.get("description", "")
        impact = strength.get("impact", "medium")
        evidence = strength.get("evidence", [])

        # Impact emoji and text
        impact_display = {
            "high": "🔥 높음",
            "medium": "💫 중간",
            "low": "✨ 낮음"
        }.get(impact, "💫 중간")

        # Format evidence as list
        evidence_html = ""
        if evidence:
            evidence_html = "<ul style='margin: 0; padding-left: 20px;'>"
            for ev in evidence[:2]:
                evidence_html += f"<li style='margin-bottom: 4px;'>{ev}</li>"
            evidence_html += "</ul>"
        else:
            evidence_html = "-"

        rows.append([category, desc, impact_display, evidence_html])

    # Render as HTML table
    lines.extend(GameRenderer.render_html_table(
        headers=headers,
        rows=rows,
        title="",
        description="",
        striped=True,
        escape_cells=False
    ))
    lines.append("")

    return lines


def _render_improvements_table(improvements: List[Any]) -> List[str]:
    """Render improvements table."""
    lines = [
        "#### 🎯 성장 기회",
        "",
    ]

    # Build table data
    headers = ["분야", "설명", "우선순위", "개선 방안"]
    rows = []

    for improvement in improvements[:5]:
        category = improvement.get("category", "")
        desc = improvement.get("description", "")
        priority = improvement.get("priority", "medium")
        suggestions = improvement.get("suggestions", [])

        # Priority emoji and text
        priority_display = {
            "critical": "🚨 긴급",
            "important": "⚡ 중요",
            "nice-to-have": "💡 권장"
        }.get(priority, "⚡ 중요")

        # Format suggestions as list
        suggestions_html = ""
        if suggestions:
            suggestions_html = "<ul style='margin: 0; padding-left: 20px;'>"
            for sug in suggestions[:3]:
                suggestions_html += f"<li style='margin-bottom: 4px;'>{sug}</li>"
            suggestions_html += "</ul>"
        else:
            suggestions_html = "-"

        rows.append([category, desc, priority_display, suggestions_html])

    # Render as HTML table
    lines.extend(GameRenderer.render_html_table(
        headers=headers,
        rows=rows,
        title="",
        description="",
        striped=True,
        escape_cells=False
    ))
    lines.append("")

    return lines


def _render_growth_indicators_table(growth_indicators: List[Any]) -> List[str]:
    """Render growth indicators table."""
    lines = [
        "#### 📈 성장 지표",
        "",
    ]

    # Build table data
    headers = ["측면", "진행 상황 요약"]
    rows = []

    for indicator in growth_indicators[:5]:
        aspect = indicator.get("aspect", "")
        progress_summary = indicator.get("progress_summary", "")
        rows.append([f"🚀 {aspect}", progress_summary])

    # Render as HTML table
    lines.extend(GameRenderer.render_html_table(
        headers=headers,
        rows=rows,
        title="",
        description="",
        striped=True,
        escape_cells=False
    ))
    lines.append("")

    return lines


__all__ = ["generate_repository_breakdown"]
