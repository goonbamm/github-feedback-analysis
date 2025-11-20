"""Cache management command for GitHub Feedback Analysis CLI.

This module contains the command for clearing the API response cache.
"""

import typer

from ...console import Console

console = Console()


def clear_cache() -> None:
    """Clear the API response cache.

    This can help resolve issues with stale or corrupted cached data
    that may cause JSON parsing errors or other unexpected behavior.

    Examples:
        gfa clear-cache
    """
    from ...api_client import GitHubApiClient

    console.print("[info]Clearing API cache...[/]")
    GitHubApiClient.clear_cache()


def register_command(app: typer.Typer) -> None:
    """Register the clear-cache command with the CLI app."""
    app.command(name="clear-cache")(clear_cache)
