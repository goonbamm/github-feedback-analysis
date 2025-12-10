"""Report sections for review reports."""

from .character_stats import render_character_stats
from .code_changes import render_code_changes_visualization
from .personal_development import render_personal_development
from .pr_activity import render_pr_activity_timeline
from .statistics import render_statistics_dashboard

__all__ = [
    "render_character_stats",
    "render_personal_development",
    "render_statistics_dashboard",
    "render_pr_activity_timeline",
    "render_code_changes_visualization",
]
