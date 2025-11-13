"""Helper utilities for building GitHub API request parameters.

This module provides reusable parameter builders to eliminate hardcoded
API parameter dictionaries across the codebase.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from github_feedback.constants import API_DEFAULTS


def build_list_params(
    state: str = "all",
    sort: str = "created",
    direction: str = "desc",
    per_page: Optional[int] = None,
    **kwargs: Any,
) -> Dict[str, Any]:
    """Build common parameters for GitHub list API endpoints.

    Args:
        state: Filter by state (all, open, closed). Defaults to "all".
        sort: Sort field (created, updated, comments). Defaults to "created".
        direction: Sort direction (asc, desc). Defaults to "desc".
        per_page: Items per page (1-100). Defaults to API_DEFAULTS['per_page'].
        **kwargs: Additional parameters to merge into the result.

    Returns:
        Dictionary of API request parameters.

    Examples:
        >>> build_list_params()
        {'state': 'all', 'sort': 'created', 'direction': 'desc', 'per_page': 100}

        >>> build_list_params(state='open', per_page=50)
        {'state': 'open', 'sort': 'created', 'direction': 'desc', 'per_page': 50}

        >>> build_list_params(state='closed', page=2)
        {'state': 'closed', 'sort': 'created', 'direction': 'desc', 'per_page': 100, 'page': 2}
    """
    params: Dict[str, Any] = {
        "state": state,
        "sort": sort,
        "direction": direction,
        "per_page": per_page if per_page is not None else API_DEFAULTS["per_page"],
    }
    params.update(kwargs)
    return params


def build_pagination_params(
    per_page: Optional[int] = None,
    page: Optional[int] = None,
    **kwargs: Any,
) -> Dict[str, Any]:
    """Build pagination parameters for GitHub API endpoints.

    Args:
        per_page: Items per page (1-100). Defaults to API_DEFAULTS['per_page'].
        page: Page number (1-based). If None, not included in params.
        **kwargs: Additional parameters to merge into the result.

    Returns:
        Dictionary of pagination parameters.

    Examples:
        >>> build_pagination_params()
        {'per_page': 100}

        >>> build_pagination_params(page=2)
        {'per_page': 100, 'page': 2}

        >>> build_pagination_params(per_page=50, page=3)
        {'per_page': 50, 'page': 3}
    """
    params: Dict[str, Any] = {
        "per_page": per_page if per_page is not None else API_DEFAULTS["per_page"],
    }
    if page is not None:
        params["page"] = page
    params.update(kwargs)
    return params


def build_commits_params(
    sha: Optional[str] = None,
    path: Optional[str] = None,
    since: Optional[str] = None,
    until: Optional[str] = None,
    per_page: Optional[int] = None,
    **kwargs: Any,
) -> Dict[str, Any]:
    """Build parameters for commits API endpoint.

    Args:
        sha: SHA or branch to start listing commits from.
        path: Only commits containing this file path will be returned.
        since: Only commits after this date (ISO 8601 format).
        until: Only commits before this date (ISO 8601 format).
        per_page: Items per page (1-100). Defaults to API_DEFAULTS['per_page'].
        **kwargs: Additional parameters to merge into the result.

    Returns:
        Dictionary of commits API parameters.

    Examples:
        >>> build_commits_params(sha='main')
        {'per_page': 100, 'sha': 'main'}

        >>> build_commits_params(since='2024-01-01T00:00:00Z', per_page=50)
        {'per_page': 50, 'since': '2024-01-01T00:00:00Z'}
    """
    params: Dict[str, Any] = {
        "per_page": per_page if per_page is not None else API_DEFAULTS["per_page"],
    }
    if sha is not None:
        params["sha"] = sha
    if path is not None:
        params["path"] = path
    if since is not None:
        params["since"] = since
    if until is not None:
        params["until"] = until
    params.update(kwargs)
    return params
