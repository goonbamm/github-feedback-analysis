"""Shared utility helpers for the GitHub feedback toolkit."""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Iterable, Iterator, TypeVar
from urllib.parse import urlparse

T = TypeVar('T')

logger = logging.getLogger(__name__)

__all__ = [
    "truncate_patch",
    "limit_items",
    "validate_pat_format",
    "validate_url",
    "validate_repo_format",
    "validate_months",
    "safe_truncate_str",
    "display_width",
    "pad_to_width",
    "FileSystemManager",
]


def display_width(text: str) -> int:
    """Calculate the display width of a string, accounting for wide characters.

    Korean, Chinese, Japanese characters and some emojis take up 2 display columns,
    while ASCII characters take up 1 column.

    Args:
        text: String to measure

    Returns:
        Display width in columns
    """
    width = 0
    for char in text:
        # Check if character is wide (CJK, fullwidth, emoji, etc.)
        if ord(char) > 0x1100:  # Rough heuristic: chars above this are often wide
            # More precise check for common wide character ranges
            code = ord(char)
            # Hangul, CJK, Fullwidth forms, Emoji, etc.
            if (0x1100 <= code <= 0x11FF or  # Hangul Jamo
                0x2E80 <= code <= 0x9FFF or  # CJK
                0xAC00 <= code <= 0xD7AF or  # Hangul Syllables
                0xF900 <= code <= 0xFAFF or  # CJK Compatibility
                0xFE30 <= code <= 0xFE6F or  # CJK Compatibility Forms
                0xFF00 <= code <= 0xFF60 or  # Fullwidth Forms
                0xFFE0 <= code <= 0xFFE6 or  # Fullwidth symbols
                0x1F000 <= code <= 0x1F9FF):  # Emoji and symbols
                width += 2
            else:
                width += 1
        else:
            width += 1
    return width


def pad_to_width(text: str, target_width: int, align: str = 'left') -> str:
    """Pad a string to a target display width, accounting for wide characters.

    Args:
        text: String to pad
        target_width: Target display width in columns
        align: Alignment ('left', 'right', or 'center')

    Returns:
        Padded string
    """
    current_width = display_width(text)
    padding_needed = target_width - current_width

    if padding_needed <= 0:
        return text

    if align == 'right':
        return ' ' * padding_needed + text
    elif align == 'center':
        left_pad = padding_needed // 2
        right_pad = padding_needed - left_pad
        return ' ' * left_pad + text + ' ' * right_pad
    else:  # left (default)
        return text + ' ' * padding_needed


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


def limit_items(items: Iterable[T], max_items: int) -> Iterator[T]:
    """Yield at most ``max_items`` items from ``items``.

    This helper keeps token usage predictable by constraining list expansion in
    prompts and summaries. Negative limits yield all items to avoid surprising
    behaviour during tests.

    Args:
        items: Iterable of items to limit
        max_items: Maximum number of items to yield (negative means all)

    Yields:
        Items from the input iterable, up to max_items
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
    from .constants import REGEX_PATTERNS
    if not REGEX_PATTERNS['pat_format'].match(pat):
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


class FileSystemManager:
    """Centralized file system operations with consistent error handling.

    This class provides utility methods for common file system operations
    with consistent error handling and logging across the codebase.
    """

    @staticmethod
    def ensure_directory(path: Path) -> Path:
        """Create directory with parents if it doesn't exist, with error handling.

        This method consolidates the directory creation pattern used throughout
        the codebase, providing consistent error handling and logging.

        Args:
            path: Path to the directory to create.

        Returns:
            The created or existing directory path.

        Raises:
            OSError: If directory creation fails due to OS-level issues.
            PermissionError: If lacking permissions to create the directory.

        Example:
            >>> from pathlib import Path
            >>> output_dir = FileSystemManager.ensure_directory(Path("reports/2024"))
        """
        try:
            path.mkdir(parents=True, exist_ok=True)
            return path
        except (OSError, PermissionError) as exc:
            logger.error(f"Failed to create directory {path}: {exc}")
            raise

    @staticmethod
    def ensure_parent_directory(file_path: Path) -> Path:
        """Ensure the parent directory of a file exists.

        Args:
            file_path: Path to a file whose parent directory should exist.

        Returns:
            The parent directory path.

        Raises:
            OSError: If directory creation fails.
            PermissionError: If lacking permissions.

        Example:
            >>> file_path = Path("reports/2024/metrics.json")
            >>> FileSystemManager.ensure_parent_directory(file_path)
        """
        parent = file_path.parent
        return FileSystemManager.ensure_directory(parent)
