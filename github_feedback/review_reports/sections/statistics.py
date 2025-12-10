"""Statistics dashboard section rendering."""

from __future__ import annotations

from typing import List

from ...game_elements import GameRenderer
from ..data_loader import StoredReview


def render_statistics_dashboard(reviews: List[StoredReview]) -> List[str]:
    """Render key metrics dashboard with HTML visual cards."""
    lines: List[str] = []

    # Calculate statistics
    total_prs = len(reviews)
    total_additions = sum(r.additions for r in reviews)
    total_deletions = sum(r.deletions for r in reviews)
    total_files_changed = sum(r.changed_files for r in reviews)
    avg_additions = total_additions // total_prs if total_prs > 0 else 0
    avg_deletions = total_deletions // total_prs if total_prs > 0 else 0

    # Count authors
    unique_authors = len(set(r.author for r in reviews))

    lines.append("## 📊 핵심 지표 대시보드")
    lines.append("")

    # Build metrics cards
    metrics_data = [
        {"title": "총 PR 수", "value": f"{total_prs}개", "emoji": "📝", "color": "#667eea"},
        {"title": "참여 인원", "value": f"{unique_authors}명", "emoji": "👥", "color": "#764ba2"},
        {"title": "총 코드 추가", "value": f"+{total_additions:,}줄", "emoji": "➕", "color": "#10b981"},
        {"title": "총 코드 삭제", "value": f"-{total_deletions:,}줄", "emoji": "➖", "color": "#ef4444"},
        {"title": "변경된 파일", "value": f"{total_files_changed:,}개", "emoji": "📁", "color": "#f59e0b"},
        {
            "title": "평균 코드 변경",
            "value": f"+{avg_additions}/-{avg_deletions}줄",
            "emoji": "📈",
            "color": "#8b5cf6",
        },
    ]

    lines.extend(GameRenderer.render_metric_cards(metrics_data, columns=3))

    lines.append("---")
    lines.append("")

    return lines


__all__ = ["render_statistics_dashboard"]
