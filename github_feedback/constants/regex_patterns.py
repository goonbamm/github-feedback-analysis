"""Regular expression patterns for validation and text processing."""

from __future__ import annotations

import re

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
# Regex Patterns (Compiled)
# =============================================================================

# Compiled regex patterns for performance
REGEX_PATTERNS = {
    # Text formatting patterns
    'emoji_prefix': re.compile(r'^[\U0001F300-\U0001F9FF\s]+'),  # Remove leading emojis
    'special_chars_suffix': re.compile(r'[.,!?\s]+$'),  # Remove trailing punctuation
    'whitespace_normalize': re.compile(r'\s+'),  # Normalize whitespace
    'pr_number': re.compile(r'PR #(\d+)'),  # Extract PR number from text

    # Commit message patterns
    'conventional_commit': re.compile(r'^(feat|fix|docs|style|refactor|test|chore|perf|ci|build|revert)', re.IGNORECASE),
    'imperative_commit': re.compile(r'^(Add|Fix|Update|Refactor|Remove|Implement|Improve|Optimize)'),

    # Issue patterns
    'bug_keywords': re.compile(r'\b(bug|error|crash|fail|broken|issue)\b', re.IGNORECASE),
    'feature_keywords': re.compile(r'\b(feature|enhancement|improve|add|request)\b', re.IGNORECASE),
    'question_keywords': re.compile(r'\b(question|how|why|documentation|docs)\b', re.IGNORECASE),

    # Review patterns - constructive
    'suggestion_markers': re.compile(r'어떨까요|고려해|제안|추천', re.IGNORECASE),
    'example_markers': re.compile(r'예시|예를 들어|이렇게|다음과 같이', re.IGNORECASE),
    'positive_emojis': re.compile(r'👍|✅|💯|🎉|😊|👏'),
    'positive_words': re.compile(r'좋|훌륭|멋|잘|감사|고마|수고', re.IGNORECASE),

    # Review patterns - harsh
    'harsh_words': re.compile(r'잘못|틀렸|오류', re.IGNORECASE),
    'demanding_words': re.compile(r'다시|반드시|꼭|절대|필수', re.IGNORECASE),

    # Issue patterns - references
    'issue_reference': re.compile(r'(#\d+|http|related|참고)', re.IGNORECASE),
    'pr_reference': re.compile(r'PR\s*#\d+', re.IGNORECASE),

    # Markdown patterns
    'markdown_table_row': re.compile(r'\|\s*[^|]+\s*\|\s*([^|]+)\s*\|'),
    'quoted_text': re.compile(r'[\'"].*?[\'"]|「.*?」'),
    'sentence_boundary': re.compile(r'[.!?。]\s+'),

    # Validation patterns (from utils.py)
    'pat_format': re.compile(r'^[a-zA-Z0-9_]+$'),
}
