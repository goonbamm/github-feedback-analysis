"""Constants and configuration values for the GitHub feedback toolkit.

This package organizes constants into logical modules for better maintainability:
- ui_styles: Console styles, table config, display settings
- analysis_thresholds: All threshold values for analysis and awards
- limits: Collection limits, display limits, parallel config
- messages: User-facing messages and phase descriptions
- awards: Award categories, game elements, stat weights
- regex_patterns: Compiled regex patterns and validation rules
- llm_config: LLM settings, quality thresholds, prompt templates
- api_config: API pagination, HTTP status codes, retry config
- types: Enums and type definitions
"""

from __future__ import annotations

# Import all constants for backward compatibility
from github_feedback.constants.analysis_thresholds import (
    ACTIVITY_THRESHOLDS,
    AWARD_ACHIEVEMENT_THRESHOLDS,
    AWARD_BALANCED_THRESHOLDS,
    AWARD_CONSISTENCY_THRESHOLDS,
    AWARD_PR_THRESHOLDS,
    COLLABORATION_LEVEL_THRESHOLDS,
    CONSISTENCY_THRESHOLDS,
    CONSISTENCY_VARIANCE_THRESHOLDS,
    CRITIQUE_THRESHOLDS,
    IMPACT_ASSESSMENT_THRESHOLDS,
    RETROSPECTIVE_CHANGE_THRESHOLDS,
    REVIEW_QUALITY_THRESHOLDS,
    TECH_STACK_THRESHOLDS,
    TREND_THRESHOLDS,
)
from github_feedback.constants.api_config import (
    API_DEFAULTS,
    API_PAGINATION,
    HTTP_STATUS,
    HTTP_STATUS_CODES,
    RETRY_CONFIG,
    THREAD_POOL_CONFIG,
)
from github_feedback.constants.awards import (
    AWARD_CATEGORIES,
    AWARD_KEYWORDS,
    BADGE_THRESHOLDS,
    FEEDBACK_SECTIONS,
    LEVEL_99_TITLES,
    SKILL_MASTERY,
    SKILL_TYPE_EMOJIS,
    SPECIALTY_TITLES,
    STAT_EMOJIS,
    STAT_NAMES_KR,
    STAT_WEIGHTS_CODE_QUALITY,
    STAT_WEIGHTS_COLLABORATION,
    STAT_WEIGHTS_GROWTH,
    STAT_WEIGHTS_PROBLEM_SOLVING,
    STAT_WEIGHTS_PRODUCTIVITY,
    TIER_SYSTEM,
    TOC_SECTIONS,
)
from github_feedback.constants.limits import (
    COLLECTION_LIMITS,
    DAYS_PER_MONTH_APPROX,
    DAYS_PER_YEAR,
    DEFAULT_CONFIG,
    DEFAULT_OUTPUT_DIR,
    DISPLAY_LIMITS,
    MONTHS_FOR_YEAR_DISPLAY,
    MONTHS_PER_YEAR,
    OUTPUT_FILES,
    PARALLEL_CONFIG,
    SECONDS_PER_DAY,
    STATISTICAL_CONSTANTS,
    TIME_CONSTANTS,
)
from github_feedback.constants.llm_config import (
    HEURISTIC_THRESHOLDS,
    LLM_DEFAULTS,
    PROMPT_TEMPLATES,
    QUALITY_THRESHOLDS,
    TEXT_LIMITS,
    VALIDATION_THRESHOLDS,
)
from github_feedback.constants.messages import (
    ANALYSIS_PHASES,
    ERROR_MESSAGES,
    INFO_MESSAGES,
    SUCCESS_MESSAGES,
)
from github_feedback.constants.regex_patterns import (
    PAT_PATTERNS,
    REGEX_PATTERNS,
    REPO_FORMAT_PATTERN,
    URL_PATTERN,
)
from github_feedback.constants.types import TaskType
from github_feedback.constants.ui_styles import (
    CONSOLE_STYLES,
    PROGRESS_REPORTING,
    SPINNERS,
    TABLE_CONFIG,
    TEXT_DISPLAY_LIMITS,
)

# Export all for convenient imports
__all__ = [
    # Types
    "TaskType",
    # UI Styles
    "CONSOLE_STYLES",
    "SPINNERS",
    "TABLE_CONFIG",
    "TEXT_DISPLAY_LIMITS",
    "PROGRESS_REPORTING",
    # Analysis Thresholds
    "ACTIVITY_THRESHOLDS",
    "CONSISTENCY_THRESHOLDS",
    "TREND_THRESHOLDS",
    "AWARD_CONSISTENCY_THRESHOLDS",
    "AWARD_BALANCED_THRESHOLDS",
    "AWARD_PR_THRESHOLDS",
    "RETROSPECTIVE_CHANGE_THRESHOLDS",
    "IMPACT_ASSESSMENT_THRESHOLDS",
    "CRITIQUE_THRESHOLDS",
    "COLLABORATION_LEVEL_THRESHOLDS",
    "REVIEW_QUALITY_THRESHOLDS",
    "CONSISTENCY_VARIANCE_THRESHOLDS",
    "TECH_STACK_THRESHOLDS",
    "AWARD_ACHIEVEMENT_THRESHOLDS",
    # Limits
    "COLLECTION_LIMITS",
    "DISPLAY_LIMITS",
    "PARALLEL_CONFIG",
    "DEFAULT_CONFIG",
    "DEFAULT_OUTPUT_DIR",
    "OUTPUT_FILES",
    "SECONDS_PER_DAY",
    "DAYS_PER_MONTH_APPROX",
    "DAYS_PER_YEAR",
    "MONTHS_PER_YEAR",
    "MONTHS_FOR_YEAR_DISPLAY",
    "TIME_CONSTANTS",
    "STATISTICAL_CONSTANTS",
    # Messages
    "ANALYSIS_PHASES",
    "ERROR_MESSAGES",
    "SUCCESS_MESSAGES",
    "INFO_MESSAGES",
    # Awards
    "AWARD_CATEGORIES",
    "AWARD_KEYWORDS",
    "TOC_SECTIONS",
    "FEEDBACK_SECTIONS",
    "LEVEL_99_TITLES",
    "TIER_SYSTEM",
    "SPECIALTY_TITLES",
    "STAT_EMOJIS",
    "STAT_NAMES_KR",
    "SKILL_TYPE_EMOJIS",
    "BADGE_THRESHOLDS",
    "SKILL_MASTERY",
    "STAT_WEIGHTS_CODE_QUALITY",
    "STAT_WEIGHTS_COLLABORATION",
    "STAT_WEIGHTS_PROBLEM_SOLVING",
    "STAT_WEIGHTS_PRODUCTIVITY",
    "STAT_WEIGHTS_GROWTH",
    # Regex Patterns
    "PAT_PATTERNS",
    "REPO_FORMAT_PATTERN",
    "URL_PATTERN",
    "REGEX_PATTERNS",
    # LLM Config
    "LLM_DEFAULTS",
    "TEXT_LIMITS",
    "HEURISTIC_THRESHOLDS",
    "PROMPT_TEMPLATES",
    "QUALITY_THRESHOLDS",
    "VALIDATION_THRESHOLDS",
    # API Config
    "API_PAGINATION",
    "API_DEFAULTS",
    "RETRY_CONFIG",
    "HTTP_STATUS",
    "THREAD_POOL_CONFIG",
    "HTTP_STATUS_CODES",
]
