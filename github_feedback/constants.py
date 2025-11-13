"""Constants and configuration values for the GitHub feedback toolkit."""

from __future__ import annotations

from typing import Dict, List

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
# Reporter Categories and Labels
# =============================================================================

# Award categories for organizing achievements
AWARD_CATEGORIES = {
    'basic': '🎖️ 기본 성취',
    'speed': '⚡ 속도 & 효율성',
    'collaboration': '🤝 협업 & 리뷰',
    'quality': '🎯 품질 & 안정성',
    'special': '🎨 특별 기여',
    'top_honors': '👑 최고 영예',
}

# Keywords for categorizing awards
AWARD_KEYWORDS = {
    'basic': ['다이아몬드', '플래티넘', '골드', '실버', '브론즈'],
    'speed': ['번개', '속도', '스프린터', '스피드', '스프린트', '머신'],
    'collaboration': ['협업', '리뷰', '멘토', '팀', '지식 전파', '감시자', '챔피언'],
    'quality': ['품질', '안정', '테스트', '버그', '수호자', '지킴이', '머지'],
    'special': ['문서', '리팩터링', '기능', '빅뱅', '미세', '아키텍트', '빌더', '건축가'],
    'top_honors': ['르네상스', '다재다능', '올라운더', '일관성의 왕', '균형'],
}

# Table of contents sections
TOC_SECTIONS = [
    ('📊 Executive Summary', '한눈에 보는 핵심 지표'),
    ('🏆 Awards Cabinet', '획득한 어워드'),
    ('✨ Growth Highlights', '성장 하이라이트'),
    ('📈 Monthly Trends', '월별 활동 트렌드'),
    ('💡 Detailed Feedback', '상세 피드백'),
    ('🎯 Spotlight Examples', '주요 기여 사례'),
    ('💻 Tech Stack', '기술 스택 분석'),
    ('🤝 Collaboration', '협업 네트워크'),
    ('🤔 Reflection', '회고 질문'),
    ('📊 Detailed Metrics', '상세 메트릭'),
    ('🔗 Evidence', '증거 링크'),
]

# Feedback section configurations
FEEDBACK_SECTIONS = {
    'commit': {
        'title': '### 📝 Commit Messages',
        'emoji': '✅',
        'metrics_label': '지표',
        'value_label': '값',
    },
    'pr_title': {
        'title': '### 🔀 PR Titles',
        'emoji': '✅',
        'metrics_label': '지표',
        'value_label': '값',
    },
    'review_tone': {
        'title': '### 👀 Review Tone',
        'emoji': '✅',
        'metrics_label': '지표',
        'value_label': '값',
    },
    'issue': {
        'title': '### 🐛 Issue Quality',
        'emoji': '✅',
        'metrics_label': '지표',
        'value_label': '값',
    },
}

# =============================================================================
# File and Directory Paths
# =============================================================================

DEFAULT_OUTPUT_DIR = 'reports'
PROMPTS_SUBDIR = 'prompts'

# Output file names
OUTPUT_FILES = {
    'metrics': 'metrics.json',
    'report_md': 'report.md',
    'commit_feedback': 'prompts/commit_feedback.txt',
    'pr_feedback': 'prompts/pr_feedback.txt',
    'review_feedback': 'prompts/review_feedback.txt',
    'issue_feedback': 'prompts/issue_feedback.txt',
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

# =============================================================================
# Validation Rules
# =============================================================================

# PAT format validation
PAT_PATTERNS = {
    'classic': r'^ghp_[a-zA-Z0-9]{36}$',
    'fine_grained': r'^github_pat_[a-zA-Z0-9]{22}_[a-zA-Z0-9]{59}$',
}

# Repository format validation
REPO_FORMAT_PATTERN = r'^[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+$'

# URL validation pattern
URL_PATTERN = r'^https?://'

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
# Data Collection Configuration
# =============================================================================

# Limits for data collection
COLLECTION_LIMITS = {
    'commit_messages': 100,
    'pr_titles': 100,
    'review_comments': 100,
    'issues': 100,
    'pr_examples': 3,  # Number of PR examples to show in spotlight
}

# Display limits for reporting
DISPLAY_LIMITS = {
    'feedback_examples': 3,  # Number of examples to show in feedback sections
    'medium_priority_insights': 3,  # Number of medium priority insights to show
}

# Parallel processing configuration
PARALLEL_CONFIG = {
    'max_workers_data_collection': 4,  # Concurrent data collection tasks
    'max_workers_llm_analysis': 4,  # Concurrent LLM analysis tasks
    'max_workers_yearend': 3,  # Concurrent year-end data collection tasks
    'collection_timeout': 120,  # Timeout for data collection in seconds
    'analysis_timeout': 180,  # Timeout for LLM analysis in seconds
    'yearend_timeout': 180,  # Timeout for year-end data collection in seconds
}

# =============================================================================
# Analysis Thresholds
# =============================================================================

# Activity level thresholds for insights and awards
ACTIVITY_THRESHOLDS = {
    # Commit thresholds
    'very_high_commits': 200,
    'high_commits': 100,
    'moderate_commits': 50,

    # Pull request thresholds
    'very_high_prs': 50,
    'high_prs': 30,
    'moderate_prs': 10,

    # Review thresholds
    'very_high_reviews': 50,
    'high_reviews': 20,
    'moderate_reviews': 10,

    # Issue thresholds
    'moderate_issues': 20,

    # Code change thresholds
    'very_large_pr': 10000,  # Lines changed
    'large_pr': 1000,  # Lines changed

    # Ratio thresholds
    'high_commits_per_pr': 5,
    'high_review_ratio': 2,  # Reviews / PRs
    'high_merge_rate': 0.8,  # 80% merge rate

    # Collaboration thresholds
    'moderate_doc_prs': 3,
    'moderate_test_prs': 5,
    'feature_pr_threshold': 5,
}

# Consistency score interpretation thresholds
CONSISTENCY_THRESHOLDS = {
    'very_consistent': 0.7,  # Above this is very consistent
    'inconsistent': 0.3,  # Below this is inconsistent
}

# Trend analysis thresholds
TREND_THRESHOLDS = {
    'increasing_multiplier': 1.2,  # 20% increase
    'decreasing_multiplier': 0.8,  # 20% decrease
    'minimum_months_for_trend': 3,  # Need at least 3 months for trend analysis
}

# =============================================================================
# API and HTTP Configuration
# =============================================================================

# Retry configuration
RETRY_CONFIG = {
    'backoff_base': 2,  # Exponential backoff base (2^attempt)
    'max_retries': 3,
}

# HTTP status codes
HTTP_STATUS = {
    'unauthorized': 401,
    'retryable_errors': (403, 429, 500, 502, 503, 504),
}

# Thread pool configuration
THREAD_POOL_CONFIG = {
    'max_workers_pr_fetch': 5,
    'max_workers_commit_branches': 3,
    'test_connection_timeout': 10,
}

# =============================================================================
# LLM Configuration
# =============================================================================

LLM_DEFAULTS = {
    'timeout': 60,
    'max_retries': 3,
    'max_files_in_prompt': 10,
    'max_patch_lines_per_file': 20,
    'max_files_with_patch_snippets': 5,
    'sample_size_commits': 20,
    'sample_size_prs': 20,
    'sample_size_reviews': 15,
    'sample_size_issues': 15,
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
}

# =============================================================================
# Prompt Templates
# =============================================================================

PROMPT_TEMPLATES = {
    'context_header': """Repository: {repo}
Period: {period}

""",
    'summary_section': """Summary:
{summary}

""",
    'metrics_section': """Metrics:
{metrics}

""",
    'highlights_section': """Growth Highlights:
{highlights}

""",
}
