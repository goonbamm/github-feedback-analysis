"""Cache command for GitHub feedback toolkit."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from github_feedback.console import Console


class CacheCommand:
    """Handles cache management commands."""

    def __init__(self, console: Console):
        """Initialize the command.

        Args:
            console: Console instance for output
        """
        self.console = console

    def clear_cache(self) -> None:
        """Clear the API response cache.

        This can help resolve issues with stale or corrupted cached data
        that may cause JSON parsing errors or other unexpected behavior.

        Examples:
            gfa clear-cache
        """
        from github_feedback.api_client import GitHubApiClient

        self.console.print("[info]Clearing API cache...[/]")
        GitHubApiClient.clear_cache()
