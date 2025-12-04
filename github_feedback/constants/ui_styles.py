"""UI styles and display configuration constants."""

from __future__ import annotations

# =============================================================================
# Console Styles and UI Elements
# =============================================================================

# Console style templates
CONSOLE_STYLES = {
    'accent': '[accent]{}[/]',
    'success': '[success]{}[/]',
    'warning': '[warning]{}[/]',
    'danger': '[danger]{}[/]',
    'info': '[info]{}[/]',
    'muted': '[muted]{}[/]',
    'title': '[title]{}[/]',
    'repo': '[repo]{}[/]',
    'label': '[label]{}[/]',
    'value': '[value]{}[/]',
}

# Spinner types for status indicators
SPINNERS = {
    'bouncing': 'bouncingBar',
    'dots': 'dots',
    'line': 'line',
    'arc': 'arc',
    'arrow': 'arrow',
    'pulse': 'pulse',
}

# =============================================================================
# Table Configuration
# =============================================================================

TABLE_CONFIG = {
    'box_style': 'ROUNDED',
    'header_style': 'bold cyan',
    'index_style': 'dim',
    'index_width': 3,
    'activity_style': 'success',
    'description_max_length': 50,
    'description_max_length_with_rank': 45,  # Shorter for tables with rank column
}

# =============================================================================
# Display & Formatting Constants
# =============================================================================

# Text truncation and display limits
TEXT_DISPLAY_LIMITS = {
    'comment_preview_length': 150,  # Truncate comments to 150 chars for preview
    'improved_version_length': 200,  # Truncate improved versions to 200 chars
    'title_min_meaningful_length': 10,  # Minimum length for a meaningful title
}

# Progress reporting intervals
PROGRESS_REPORTING = {
    'pr_progress_interval': 10,  # Report progress every 10 PRs
    'commit_progress_interval': 20,  # Report progress every 20 commits
}
