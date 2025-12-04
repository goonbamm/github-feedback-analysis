"""User-facing messages and analysis phase descriptions."""

from __future__ import annotations

# =============================================================================
# Analysis Phases
# =============================================================================

ANALYSIS_PHASES = {
    0: "Configuration validation",
    1: "Repository access verification",
    2: "Data collection (commits, PRs, reviews, issues)",
    3: "Metrics computation and trend analysis",
    4: "LLM-based feedback generation (commit messages, PR titles, review tone, issue quality)",
    5: "Report generation (markdown)",
}

# =============================================================================
# Error Messages
# =============================================================================

ERROR_MESSAGES = {
    'config_invalid': 'Configuration error',
    'config_missing': 'Run [accent]gfa init[/] to set up your configuration',
    'pat_invalid': 'GitHub API rejected the provided PAT',
    'pat_permissions': 'PAT requires "repo" scope for private repos or "public_repo" for public repos',
    'repo_not_found': 'Repository not found',
    'repo_invalid_format': 'Invalid repository format. Use owner/repo format (e.g., torvalds/linux)',
    'llm_connection_failed': 'Detailed feedback analysis failed: Connection refused',
    'llm_server_down': 'LLM server is not running or unreachable',
    'no_activity': 'No significant activity detected during the analysis period',
    'no_suggestions': 'No repository suggestions found',
}

# =============================================================================
# Success Messages
# =============================================================================

SUCCESS_MESSAGES = {
    'config_saved': 'Configuration saved successfully',
    'analysis_complete': 'Analysis complete',
    'report_generated': 'Report generated successfully',
    'repo_selected': 'Selected',
    'data_collected': 'Data collection complete',
}

# =============================================================================
# Info Messages
# =============================================================================

INFO_MESSAGES = {
    'fetching_repos': 'Fetching repository suggestions...',
    'analyzing_repos': 'Analyzing repositories...',
    'collecting_data': 'Collecting data from GitHub...',
    'computing_metrics': 'Computing metrics...',
    'generating_feedback': 'Generating feedback...',
    'creating_report': 'Creating report...',
    'try_manual_repo': 'Try manually specifying a repository with [accent]--repo[/]',
    'selection_cancelled': 'Selection cancelled.',
}
