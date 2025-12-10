"""PR activity timeline section rendering."""

from __future__ import annotations

import html
from typing import List

from ...game_elements import GameRenderer
from ..data_loader import StoredReview


def render_pr_activity_timeline(reviews: List[StoredReview]) -> List[str]:
    """Render PR activity timeline using HTML table."""
    if not reviews:
        return []

    lines: List[str] = []
    lines.append("## 📅 PR 활동 타임라인")
    lines.append("")
    lines.append("> PR 활동의 시간 순서를 확인하세요")
    lines.append("")

    # Build table data - show all PRs in chronological order
    headers = ["#", "PR 번호", "제목", "작성자", "생성일", "코드 변경", "링크"]
    rows = []

    for idx, review in enumerate(reviews, 1):
        date_str = review.created_at.strftime("%Y-%m-%d")
        title_raw = review.title[:50] + "..." if len(review.title) > 50 else review.title
        title_short = html.escape(title_raw, quote=False)

        # Code changes with color indicators
        code_changes = f'<span style="color: #10b981;">+{review.additions}</span> / <span style="color: #ef4444;">-{review.deletions}</span>'

        # Author with emoji
        author_display = f"👤 {html.escape(review.author, quote=False)}"

        # Link
        if review.html_url:
            url = html.escape(review.html_url, quote=True)
            link = f"[보기]({url})"
        else:
            link = "-"

        rows.append(
            [
                str(idx),
                f"#{review.number}",
                title_short,
                author_display,
                html.escape(date_str, quote=False),
                code_changes,
                link,
            ]
        )

    # Render as HTML table
    lines.extend(
        GameRenderer.render_html_table(
            headers=headers, rows=rows, title="", description="", striped=True, escape_cells=False
        )
    )

    lines.append("---")
    lines.append("")

    return lines


__all__ = ["render_pr_activity_timeline"]
