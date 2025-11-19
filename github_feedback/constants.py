"""Constants and configuration values for the GitHub feedback toolkit."""

from __future__ import annotations

from enum import Enum
from typing import Dict, List


# =============================================================================
# Task Types
# =============================================================================

class TaskType(str, Enum):
    """Types of parallel tasks for consistent error handling and messaging."""

    COLLECTION = "collection"
    ANALYSIS = "analysis"

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
    'speed': ['번개', '속도', '스프린터', '스피드', '스프린트', '머신', '광속', '생산성'],
    'collaboration': ['협업', '리뷰', '멘토', '팀', '지식 전파', '감시자', '챔피언', '전파자', '매니아', '광신도'],
    'quality': ['품질', '안정', '테스트', '버그', '수호자', '지킴이', '머지', '옹호자', '스쿼셔'],
    'special': ['문서', '리팩터링', '기능', '빅뱅', '미세', '아키텍트', '빌더', '건축가', '화산', '공장', '영웅'],
    'top_honors': ['르네상스', '다재다능', '올라운더', '일관성의 왕', '균형', '불멸', '전설', '정복자', '얼리버드', '나이트'],
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

# Output file names (only actively used files)
OUTPUT_FILES = {
    'metrics': 'metrics.json',
    'report_md': 'report.md',
    # Note: prompt files (commit_feedback, pr_feedback, etc.) are no longer generated
    # Note: PROMPTS_SUBDIR removed as prompts folder is no longer created
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
# Time Conversion Constants
# =============================================================================

SECONDS_PER_DAY = 24 * 3600
DAYS_PER_MONTH_APPROX = 30  # Approximate days per month for calculations
DAYS_PER_YEAR = 365  # Days per year for calculations
MONTHS_PER_YEAR = 12
MONTHS_FOR_YEAR_DISPLAY = 24  # Display in years if >= 24 months

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

# Award calculation thresholds - Consistency awards
AWARD_CONSISTENCY_THRESHOLDS = {
    'consistent_months': 6,  # Minimum months for consistency award
    'consistent_activity_per_month': 20,  # Minimum activity per month
    'sprint_months': 3,  # Minimum months for sprint award
    'sprint_velocity': 30,  # Minimum velocity for sprint award
}

# Award calculation thresholds - Balanced contributor awards
AWARD_BALANCED_THRESHOLDS = {
    'allrounder_commits': 50,  # Minimum commits for all-rounder award
    'allrounder_prs': 15,  # Minimum PRs for all-rounder award
    'allrounder_reviews': 15,  # Minimum reviews for all-rounder award
    'balanced_min_ratio': 0.2,  # Minimum ratio for balanced contribution (20%)
    'balanced_max_ratio': 0.5,  # Maximum ratio for balanced contribution (50%)
    'renaissance_commits': 100,  # Minimum commits for renaissance developer
    'renaissance_prs': 30,  # Minimum PRs for renaissance developer
    'renaissance_reviews': 50,  # Minimum reviews for renaissance developer
    'renaissance_issues': 10,  # Minimum issues for renaissance developer
}

# Award calculation thresholds - PR characteristics
AWARD_PR_THRESHOLDS = {
    'micro_pr_size': 50,  # Maximum lines changed for micro PR
    'micro_pr_count': 10,  # Minimum count of small PRs for micro-commit artist award
}

# =============================================================================
# Retrospective Analysis Thresholds
# =============================================================================

# Change significance thresholds for time comparisons
RETROSPECTIVE_CHANGE_THRESHOLDS = {
    'major_change_pct': 50,  # > 50% change is major
    'moderate_change_pct': 20,  # > 20% change is moderate
    # <= 20% change is minor
}

# Impact assessment thresholds for different contribution types
IMPACT_ASSESSMENT_THRESHOLDS = {
    # Commit impact levels
    'commits_high_impact': 200,  # > 200 commits is high impact
    'commits_medium_impact': 50,  # > 50 commits is medium impact
    # <= 50 commits is low impact

    # PR impact levels
    'prs_high_impact': 50,  # > 50 PRs is high impact
    'prs_medium_impact': 20,  # > 20 PRs is medium impact
    # <= 20 PRs is low impact

    # Review impact levels
    'reviews_high_impact': 100,  # > 100 reviews is high impact
    'reviews_medium_impact': 30,  # > 30 reviews is medium impact
    # <= 30 reviews is low impact
}

# =============================================================================
# API and HTTP Configuration
# =============================================================================

# GitHub API pagination defaults
API_PAGINATION = {
    'default_per_page': 100,
    'max_per_page': 100,
    'min_per_page': 1,
    'max_pages': 100,
}

# GitHub API request defaults
API_DEFAULTS = {
    'per_page': 100,
    'state': 'all',
    'sort': 'created',
    'direction': 'desc',
    'cache_expire_seconds': 3600,  # 1 hour
}

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

# Text processing limits
TEXT_LIMITS = {
    'commit_message_display_length': 100,  # Max length for displaying commit messages
    'pr_body_min_quality_length': 100,  # Min length for considering PR body as detailed
    'max_samples_mentioned_in_prompt': 20,  # Max samples mentioned in LLM prompts
    'example_display_limit': 3,  # Number of good/poor examples to collect
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
# Heuristic Analysis Thresholds
# =============================================================================

# Thresholds for heuristic-based fallback analysis
HEURISTIC_THRESHOLDS = {
    # PR size thresholds
    'pr_very_large': 1000,  # Total lines changed (additions + deletions)
    'pr_small': 100,  # Total lines changed

    # PR body quality
    'pr_body_min_quality_length': 100,  # Minimum length for detailed PR body

    # Commit message quality
    'commit_min_length': 10,
    'commit_max_length': 72,
    'commit_too_long': 100,
    'commit_min_body_length': 20,

    # PR title quality
    'pr_title_min_length': 15,
    'pr_title_max_length': 80,
    'pr_title_min_words': 4,

    # Issue quality
    'issue_body_short': 100,
    'issue_body_detailed': 200,
    'issue_good_score': 4,

    # Review quality
    'review_good_score': 2,

    # LLM settings
    'llm_temperature': 0.3,
    'llm_test_max_tokens': 10,
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

# =============================================================================
# Game Elements Configuration
# =============================================================================

# 게임 컨셉 가이드라인:
# - 종합 보고서 (Year in Review): 강한 게임 은유 (던전/퀘스트/경험치) + 99레벨 시스템
# - 개별 보고서 (Review Reporter): 중간 게임 요소 (스킬/레벨) + 티어 시스템
# - 일반 보고서 (Reporter): 약한 게임 요소 (스탯만) + 티어 시스템

# 99레벨 시스템 (종합 보고서용)
LEVEL_99_TITLES = [
    (500, 99, "전설의 코드마스터", "👑"),
    (300, 80, "그랜드마스터", "💎"),
    (150, 60, "마스터", "🏆"),
    (75, 40, "전문가", "⭐"),
    (30, 20, "숙련자", "💫"),
    (10, 10, "초보자", "🌱"),
    (0, 1, "견습생", "✨"),
]

# 티어 시스템 (개별/일반 보고서용)
TIER_SYSTEM = [
    (90, 6, "그랜드마스터", "👑"),
    (75, 5, "마스터", "🏆"),
    (60, 4, "전문가", "⭐"),
    (40, 3, "숙련자", "💎"),
    (20, 2, "견습생", "🎓"),
    (0, 1, "초보자", "🌱"),
]

# 특성 타이틀 매핑
SPECIALTY_TITLES = {
    "코드 품질": "코드 아키텍트",
    "협업력": "팀 플레이어",
    "문제 해결력": "문제 해결사",
    "생산성": "스피드 러너",
    "성장성": "라이징 스타",
}

# 스탯 이모지 매핑
STAT_EMOJIS = {
    "code_quality": "💻",
    "collaboration": "🤝",
    "problem_solving": "🧩",
    "productivity": "⚡",
    "consistency": "📅",
    "growth": "📈",
}

# 스탯 한글 이름
STAT_NAMES_KR = {
    "code_quality": "코드 품질",
    "collaboration": "협업력",
    "problem_solving": "문제 해결력",
    "productivity": "생산성",
    "consistency": "꾸준함",
    "growth": "성장성",
}

# 스킬 타입 이모지
SKILL_TYPE_EMOJIS = {
    "패시브": "🟢",
    "액티브": "🔵",
    "성장중": "🟡",
    "미습득": "🔴",
}

# 뱃지 임계값
BADGE_THRESHOLDS = {
    # 스탯 기반 뱃지 (80 이상)
    'stat_threshold': 80,

    # 활동량 기반 뱃지
    'commit_marathon': 200,
    'commit_active': 100,
    'pr_master': 50,
    'pr_contributor': 20,
    'repo_multiverse': 10,
    'repo_crawler': 5,
}
