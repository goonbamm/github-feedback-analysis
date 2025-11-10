"""Shared utility helpers for the GitHub feedback toolkit."""

from __future__ import annotations

from typing import Iterable

__all__ = ["truncate_patch", "limit_items"]


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
