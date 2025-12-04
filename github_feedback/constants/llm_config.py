"""LLM and quality analysis configuration constants."""

from __future__ import annotations

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
# Quality Ratio Thresholds
# =============================================================================

# Quality assessment thresholds used across the codebase
QUALITY_THRESHOLDS = {
    'excellent': 0.8,  # >= 80% quality is excellent
    'good': 0.7,  # >= 70% quality is good
    'acceptable': 0.6,  # >= 60% quality is acceptable
    'needs_improvement': 0.4,  # < 40% quality needs improvement
    'poor': 0.3,  # < 30% quality is poor
}

# Validation and evidence thresholds
VALIDATION_THRESHOLDS = {
    'strong': 0.7,  # >= 70% validation score is strong
    'acceptable': 0.6,  # >= 60% validation score is acceptable
    'weak': 0.4,  # < 40% validation score is weak
    'poor': 0.3,  # < 30% validation score is poor
    'min_evidence_count': 2,  # Minimum evidence/suggestions count
    'min_substantial_length': 20,  # Minimum length for substantial suggestions
    'max_hybrid_suggestions': 5,  # Maximum suggestions in hybrid analysis
}
