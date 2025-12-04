"""API, HTTP, and network configuration constants."""

from __future__ import annotations

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
# HTTP Status Codes
# =============================================================================

# Additional HTTP status codes
HTTP_STATUS_CODES = {
    'no_content': 204,  # No content response
    'not_modified': 304,  # Not modified (cache hit)
    'server_error_min': 500,  # Minimum server error code
    'no_space_errno': 28,  # ENOSPC - No space left on device (errno)
}
