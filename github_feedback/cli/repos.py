"""Repository management commands for the CLI."""

from __future__ import annotations

from typing import Optional

import typer

from . import helpers
from ..collectors.collector import Collector
from ..core.console import Console
from ..repository_display import create_repository_table

console = Console()


def list_repos(
    sort: str = typer.Option(
        "updated",
        "--sort",
        "-s",
        help="Sort field (updated, created, pushed, full_name)",
    ),
    limit: int = typer.Option(
        20,
        "--limit",
        "-l",
        help="Maximum number of repositories to display",
    ),
    org: Optional[str] = typer.Option(
        None,
        "--org",
        "-o",
        help="Filter by organization name",
    ),
) -> None:
    """List repositories accessible to the authenticated user.

    This command fetches repositories from GitHub and displays them in a
    formatted table. You can filter by organization and sort by various
    criteria.

    Examples:
        gfa list-repos
        gfa list-repos --sort stars --limit 10
        gfa list-repos --org myorganization
    """
    config = cli_helpers.load_config()

    try:
        collector = Collector(config)
    except ValueError as exc:
        console.print_error(exc)
        raise typer.Exit(code=1) from exc

    with console.status("[accent]Fetching repositories...", spinner="bouncingBar"):
        if org:
            repos = collector.list_org_repositories(org, sort)
        else:
            repos = collector.list_user_repositories(sort)

    if not repos:
        console.print("[warning]No repositories found.[/]")
        if org:
            console.print(f"[info]Organization:[/] {org}")
        raise typer.Exit(code=0)

    # Limit the results
    repos = repos[:limit]

    # Display repositories using helper function
    create_repository_table(
        repos=repos,
        title=f"{'Organization' if org else 'Your'} Repositories",
        include_rank=False,
        include_activity=False,
        console=console,
    )


def suggest_repos(
    limit: int = typer.Option(
        10,
        "--limit",
        "-l",
        help="Maximum number of suggestions",
    ),
    days: int = typer.Option(
        90,
        "--days",
        "-d",
        help="Filter repos updated within this many days",
    ),
    sort: str = typer.Option(
        "activity",
        "--sort",
        "-s",
        help="Sort criteria (updated, stars, activity)",
    ),
) -> None:
    """Suggest repositories for analysis based on activity and recency.

    This command recommends repositories that are actively maintained and
    likely to benefit from analysis. Suggestions are based on recent updates,
    stars, forks, and overall activity.

    Examples:
        gfa suggest-repos
        gfa suggest-repos --limit 5 --days 30
        gfa suggest-repos --sort stars
    """
    config = cli_helpers.load_config()

    try:
        collector = Collector(config)
    except ValueError as exc:
        console.print_error(exc)
        raise typer.Exit(code=1) from exc

    with console.status("[accent]Analyzing repositories...", spinner="bouncingBar"):
        suggestions = collector.suggest_repositories(
            limit=limit, min_activity_days=days, sort_by=sort
        )

    if not suggestions:
        console.print("[warning]No repository suggestions found.[/]")
        console.print(
            f"[info]Try increasing the activity window with [accent]--days[/] (current: {days})"
        )
        raise typer.Exit(code=0)

    # Display repository suggestions using helper function
    create_repository_table(
        repos=suggestions,
        title="Suggested Repositories for Analysis",
        include_rank=True,
        include_activity=True,
        console=console,
    )
    console.print_section_separator()
    console.print(
        "[info]To analyze a repository, use:[/] [accent]gfa feedback --repo <owner/name>[/]"
    )


def clear_cache() -> None:
    """Clear the API response cache.

    This can help resolve issues with stale or corrupted cached data
    that may cause JSON parsing errors or other unexpected behavior.

    Examples:
        gfa clear-cache
    """
    from .api_client import GitHubApiClient

    console.print("[info]Clearing API cache...[/]")
    GitHubApiClient.clear_cache()
