"""Code changes visualization section rendering."""

from __future__ import annotations

import html
from typing import List

from ...game_elements import GameRenderer
from ..data_loader import StoredReview


def render_code_changes_visualization(reviews: List[StoredReview]) -> List[str]:
    """Render code changes as visual bar charts (HTML version)."""
    if not reviews:
        return []

    lines: List[str] = []
    lines.append("## 📊 PR별 코드 변경량 분석")
    lines.append("")

    # Sort by total changes
    sorted_reviews = sorted(reviews, key=lambda r: r.additions + r.deletions, reverse=True)

    # Show top 10 PRs with most changes
    lines.append("### 상위 10개 PR (변경량 기준)")
    lines.append("")

    # Build table data
    headers = ["PR", "제목", "추가", "삭제", "총 변경", "시각화"]
    rows = []

    for review in sorted_reviews[:10]:
        total_changes = review.additions + review.deletions
        max_bar_length = 20

        # Create visual bars
        if total_changes > 0:
            add_ratio = review.additions / total_changes
            add_bar_length = int(max_bar_length * add_ratio)
            del_bar_length = max_bar_length - add_bar_length
        else:
            add_bar_length = 0
            del_bar_length = 0

        visual_bar = f"{'🟩' * add_bar_length}{'🟥' * del_bar_length}"
        title_raw = review.title[:30] + "..." if len(review.title) > 30 else review.title
        title_short = html.escape(title_raw, quote=False)

        rows.append(
            [
                f"[#{review.number}]({html.escape(review.html_url, quote=True)})",
                title_short,
                f"+{review.additions:,}",
                f"-{review.deletions:,}",
                f"{total_changes:,}",
                visual_bar,
            ]
        )

    # Render as HTML table
    lines.extend(
        GameRenderer.render_html_table(
            headers=headers, rows=rows, title="", description="", striped=True, escape_cells=False
        )
    )

    # Add distribution chart using HTML table
    lines.append("### 코드 변경량 분포")
    lines.append("")

    total_additions = sum(r.additions for r in reviews)
    total_deletions = sum(r.deletions for r in reviews)
    total_changes = total_additions + total_deletions

    # Build table data for code change distribution
    headers = ["구분", "줄 수", "비율", "시각화"]
    rows = []

    # Calculate percentages
    add_percentage = (total_additions / total_changes * 100) if total_changes > 0 else 0
    del_percentage = (total_deletions / total_changes * 100) if total_changes > 0 else 0

    # Create visual bars
    add_bar_width = int(add_percentage)
    del_bar_width = int(del_percentage)

    add_visual = f'<div style="background: linear-gradient(90deg, #10b981 0%, #059669 100%); height: 20px; width: {add_bar_width}%; border-radius: 4px;"></div>'
    del_visual = f'<div style="background: linear-gradient(90deg, #ef4444 0%, #dc2626 100%); height: 20px; width: {del_bar_width}%; border-radius: 4px;"></div>'

    rows.append(
        [
            "코드 추가",
            f"<span style='color: #10b981; font-weight: bold;'>+{total_additions:,}줄</span>",
            f"{add_percentage:.1f}%",
            add_visual,
        ]
    )
    rows.append(
        [
            "코드 삭제",
            f"<span style='color: #ef4444; font-weight: bold;'>-{total_deletions:,}줄</span>",
            f"{del_percentage:.1f}%",
            del_visual,
        ]
    )
    rows.append(["**전체 변경**", f"**{total_changes:,}줄**", "100%", ""])

    # Render as HTML table
    lines.extend(
        GameRenderer.render_html_table(
            headers=headers, rows=rows, title="", description="", striped=True, escape_cells=False
        )
    )

    lines.append("---")
    lines.append("")

    return lines


__all__ = ["render_code_changes_visualization"]
