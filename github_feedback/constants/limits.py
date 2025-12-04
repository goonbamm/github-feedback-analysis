"""Data collection and display limits configuration."""

from __future__ import annotations

# =============================================================================
# Data Collection Configuration
# =============================================================================

# Limits for data collection
COLLECTION_LIMITS = {
    'commit_messages': 100,
    'pr_titles': 100,
    'review_comments': 100,
    'issues': 100,
    'pr_examples': 3,  # Number of PR examples to show in spotlight
    'max_prs_to_process': 50,  # Maximum PRs to process for file analysis
}

# Display limits for reporting
DISPLAY_LIMITS = {
    'feedback_examples': 2,  # Number of examples to show in feedback sections (reduced for brevity)
    'medium_priority_insights': 2,  # Number of medium priority insights to show (reduced for brevity)
    'top_languages': 5,  # Number of top languages to display
    'top_reviewers': 5,  # Number of top reviewers to display
    'max_goals': 5,  # Maximum number of goals to return
    'growth_indicators': 2,  # Number of growth indicators to show per learning insight (reduced for brevity)
}

# Parallel processing configuration
PARALLEL_CONFIG = {
    'max_workers_data_collection': 3,  # Concurrent data collection tasks (Phase 1)
    'max_workers_pr_data': 2,  # Concurrent PR data processing tasks (Phase 2)
    'max_workers_llm_analysis': 4,  # Concurrent LLM analysis tasks
    'max_workers_yearend': 3,  # Concurrent year-end data collection tasks
    'max_workers_pr_review': 3,  # Concurrent PR review tasks
    'collection_timeout': 120,  # Timeout for data collection in seconds
    'analysis_timeout': 180,  # Timeout for LLM analysis in seconds
    'yearend_timeout': 180,  # Timeout for year-end data collection in seconds
    'pr_review_timeout': 180,  # Timeout for PR review in seconds
}

# =============================================================================
# Defaults
# =============================================================================

DEFAULT_CONFIG = {
    'months': 12,
    'timeout': 60,
    'max_retries': 3,
    'max_files_in_prompt': 10,
    'repo_suggestions_limit': 10,
    'min_activity_days': 90,
}

# =============================================================================
# File and Directory Paths
# =============================================================================

DEFAULT_OUTPUT_DIR = 'reports'

# Output file names (only actively used files)
OUTPUT_FILES = {
    'metrics': 'metrics.json',
    'report_md': 'report.md',
    # Note: prompt files (commit_feedback, pr_feedback, etc.) are no longer generated
    # Note: PROMPTS_SUBDIR removed as prompts folder is no longer created
}

# =============================================================================
# Time Conversion Constants
# =============================================================================

SECONDS_PER_DAY = 24 * 3600
DAYS_PER_MONTH_APPROX = 30  # Approximate days per month for calculations
DAYS_PER_YEAR = 365  # Days per year for calculations
MONTHS_PER_YEAR = 12
MONTHS_FOR_YEAR_DISPLAY = 24  # Display in years if >= 24 months

# =============================================================================
# Time & Duration Constants
# =============================================================================

# Time-related constants (in seconds)
TIME_CONSTANTS = {
    'hour_in_seconds': 3600,  # 1 hour = 3600 seconds
    'quick_merge_threshold': 3600,  # PRs merged within 1 hour are "quick merges"
}

# =============================================================================
# Statistical & Mathematical Constants
# =============================================================================

# Statistical calculation constants
STATISTICAL_CONSTANTS = {
    'min_months_for_comparison': 2,  # Need at least 2 months for comparison
    'min_months_for_trend': 3,  # Need at least 3 months for trend analysis
    'zero_division_fallback': 0,  # Fallback value when dividing by zero
}
