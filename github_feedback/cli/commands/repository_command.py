"""Repository command for GitHub feedback toolkit."""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

import typer

from github_feedback import cli_helpers
from github_feedback.collector import Collector
from github_feedback.repository_display import create_repository_table

if TYPE_CHECKING:
    from github_feedback.console import Console


class RepositoryCommand:
    """Handles repository-related commands."""

    def __init__(self, console: Console):
        """Initialize the command.

        Args:
            console: Console instance for output
        """
        self.console = console

    def list_repos(
        self,
        sort: str = "updated",
        limit: int = 20,
        org: Optional[str] = None,
    ) -> None:
        """List repositories accessible to the authenticated user.

        This command fetches repositories from GitHub and displays them in a
        formatted table. You can filter by organization and sort by various
        criteria.

        Args:
            sort: Sort field (updated, created, pushed, full_name)
            limit: Maximum number of repositories to display
            org: Filter by organization name

        Examples:
            gfa list-repos
            gfa list-repos --sort stars --limit 10
            gfa list-repos --org myorganization

        Raises:
            typer.Exit: If collector initialization fails or no repos found
        """
        config = cli_helpers.load_config()

        try:
            collector = Collector(config)
        except ValueError as exc:
            self.console.print_error(exc)
            raise typer.Exit(code=1) from exc

        with self.console.status("[accent]Fetching repositories...", spinner="bouncingBar"):
            if org:
                repos = collector.list_org_repositories(org, sort)
            else:
                repos = collector.list_user_repositories(sort)

        if not repos:
            self.console.print("[warning]No repositories found.[/]")
            if org:
                self.console.print(f"[info]Organization:[/] {org}")
            raise typer.Exit(code=0)

        # Limit the results
        repos = repos[:limit]

        # Display repositories using helper function
        create_repository_table(
            repos=repos,
            title=f"{'Organization' if org else 'Your'} Repositories",
            include_rank=False,
            include_activity=False,
            console=self.console,
        )

    def suggest_repos(
        self,
        limit: int = 10,
        days: int = 90,
        sort: str = "activity",
    ) -> None:
        """Suggest repositories for analysis based on activity and recency.

        This command recommends repositories that are actively maintained and
        likely to benefit from analysis. Suggestions are based on recent updates,
        stars, forks, and overall activity.

        Args:
            limit: Maximum number of suggestions
            days: Filter repos updated within this many days
            sort: Sort criteria (updated, stars, activity)

        Examples:
            gfa suggest-repos
            gfa suggest-repos --limit 5 --days 30
            gfa suggest-repos --sort stars

        Raises:
            typer.Exit: If collector initialization fails or no suggestions found
        """
        config = cli_helpers.load_config()

        try:
            collector = Collector(config)
        except ValueError as exc:
            self.console.print_error(exc)
            raise typer.Exit(code=1) from exc

        with self.console.status("[accent]Analyzing repositories...", spinner="bouncingBar"):
            suggestions = collector.suggest_repositories(
                limit=limit, min_activity_days=days, sort_by=sort
            )

        if not suggestions:
            self.console.print("[warning]No repository suggestions found.[/]")
            self.console.print(
                f"[info]Try increasing the activity window with [accent]--days[/] (current: {days})"
            )
            raise typer.Exit(code=0)

        # Display repository suggestions using helper function
        create_repository_table(
            repos=suggestions,
            title="Suggested Repositories for Analysis",
            include_rank=True,
            include_activity=True,
            console=self.console,
        )
        self.console.print_section_separator()
        self.console.print(
            "[info]To analyze a repository, use:[/] [accent]gfa feedback --repo <owner/name>[/]"
        )
