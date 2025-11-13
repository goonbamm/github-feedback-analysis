"""Shared utility helpers for the GitHub feedback toolkit."""

from __future__ import annotations

import re
from typing import Iterable
from urllib.parse import urlparse

__all__ = ["truncate_patch", "limit_items", "validate_pat_format", "validate_url", "validate_repo_format", "validate_months", "safe_truncate_str"]


def safe_truncate_str(text: str, max_length: int) -> str:
    """Safely truncate a string to max_length, avoiding splitting multi-byte characters.

    Args:
        text: The string to truncate
        max_length: Maximum length in characters

    Returns:
        Truncated string that won't split multi-byte UTF-8 characters
    """
    if len(text) <= max_length:
        return text

    # Truncate and handle potential multi-byte character split
    truncated = text[:max_length]
    # Encode to UTF-8, then decode with error handling to remove broken characters
    try:
        # Try encoding and decoding to verify it's valid
        truncated.encode('utf-8')
        return truncated
    except UnicodeEncodeError:
        # If there's an issue, use encode/decode with ignore to be safe
        return text.encode('utf-8')[:max_length].decode('utf-8', errors='ignore')


def truncate_patch(patch: str, max_lines: int = 12) -> str:
    """Trim diff content to a manageable snippet.

    Parameters
    ----------
    patch:
        The unified diff content returned by the GitHub API.
    max_lines:
        Maximum number of lines to keep in the snippet. The value should be at
        least 1; values lower than that are treated as 1 to ensure a non-empty
        output when a patch exists.
    """

    if not patch:
        return ""

    if max_lines < 1:
        max_lines = 1

    lines = patch.splitlines()
    if len(lines) <= max_lines:
        return patch

    head = lines[: max_lines - 1]
    head.append("...")
    return "\n".join(head)


def limit_items(items: Iterable, max_items: int):
    """Yield at most ``max_items`` items from ``items``.

    This helper keeps token usage predictable by constraining list expansion in
    prompts and summaries. Negative limits yield all items to avoid surprising
    behaviour during tests.
    """

    if max_items < 0:
        yield from items
        return

    for index, item in enumerate(items):
        if index >= max_items:
            break
        yield item


def validate_pat_format(pat: str) -> None:
    """Validate GitHub Personal Access Token format.

    Args:
        pat: The token to validate.

    Raises:
        ValueError: If the token format is invalid.
    """
    if not pat or not pat.strip():
        raise ValueError("PAT cannot be empty")

    # GitHub classic tokens start with 'ghp_' and are 40 chars total
    # GitHub fine-grained tokens start with 'github_pat_' and are longer
    # GitHub App tokens start with 'ghs_'
    # OAuth tokens don't have a specific prefix
    pat = pat.strip()

    if len(pat) < 20:
        raise ValueError("PAT appears too short to be valid")

    # Check for common mistakes
    if pat.startswith(("***", "xxx", "...")):
        raise ValueError("PAT appears to be a placeholder, not a real token")

    # Basic format check
    if not re.match(r'^[a-zA-Z0-9_]+$', pat):
        raise ValueError("PAT contains invalid characters")


def validate_url(url: str, name: str = "URL") -> None:
    """Validate URL format.

    Args:
        url: The URL to validate.
        name: Name of the URL field for error messages.

    Raises:
        ValueError: If the URL format is invalid.
    """
    if not url or not url.strip():
        raise ValueError(f"{name} cannot be empty")

    url = url.strip()

    try:
        result = urlparse(url)
        if not result.scheme:
            raise ValueError(f"{name} must include a scheme (http:// or https://)")
        if result.scheme not in ("http", "https"):
            raise ValueError(f"{name} must use http or https scheme")
        if not result.netloc:
            raise ValueError(f"{name} must include a hostname")
    except Exception as exc:
        raise ValueError(f"Invalid {name}: {exc}") from exc


def validate_repo_format(repo: str) -> None:
    """Validate GitHub repository format (owner/name).

    Args:
        repo: The repository string to validate.

    Raises:
        ValueError: If the format is invalid or contains path traversal attempts.
    """
    if not repo or not repo.strip():
        raise ValueError("Repository cannot be empty")

    repo = repo.strip()

    # Check for path traversal attempts
    if ".." in repo:
        raise ValueError("Repository name cannot contain '..' (path traversal attempt)")

    # Check for absolute paths
    if repo.startswith("/") or (len(repo) > 1 and repo[1] == ":"):  # Unix or Windows absolute path
        raise ValueError("Repository name cannot be an absolute path")

    # Must be in owner/repo format
    if "/" not in repo:
        raise ValueError("Repository must be in 'owner/repo' format (e.g., 'torvalds/linux')")

    parts = repo.split("/")
    if len(parts) != 2:
        raise ValueError("Repository must be in 'owner/repo' format with exactly one slash")

    owner, name = parts
    if not owner or not name:
        raise ValueError("Both owner and repository name must be non-empty")

    # GitHub username/org and repo name constraints
    pattern = r'^[a-zA-Z0-9_.-]+$'
    if not re.match(pattern, owner):
        raise ValueError(f"Invalid owner name '{owner}': must contain only alphanumeric, dash, dot, and underscore")
    if not re.match(pattern, name):
        raise ValueError(f"Invalid repository name '{name}': must contain only alphanumeric, dash, dot, and underscore")


def validate_months(months: int) -> None:
    """Validate months parameter.

    Args:
        months: The number of months to validate.

    Raises:
        ValueError: If months is out of valid range.
    """
    if months < 1:
        raise ValueError("Months must be at least 1")
    if months > 120:
        raise ValueError("Months cannot exceed 120 (10 years)")
