"""Helper functions for displaying repository information in tables."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from .constants import DAYS_PER_MONTH_APPROX, DAYS_PER_YEAR, TABLE_CONFIG

try:
    from rich import box
    from rich.table import Table
except ModuleNotFoundError:
    Table = None
    box = None


def format_relative_date(date_str: str) -> str:
    """Format ISO date string as relative time.

    Args:
        date_str: ISO format date string (e.g., "2024-01-15T10:30:00Z")

    Returns:
        Human-readable relative time string (e.g., "2d ago", "1mo ago")
        Returns "unknown" if parsing fails
    """
    if not date_str:
        return ""

    try:
        updated_dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        updated_dt = updated_dt.replace(tzinfo=None)
        days_ago = (datetime.now() - updated_dt).days

        if days_ago == 0:
            return "today"
        elif days_ago == 1:
            return "yesterday"
        elif days_ago < DAYS_PER_MONTH_APPROX:
            return f"{days_ago}d ago"
        elif days_ago < DAYS_PER_YEAR:
            return f"{days_ago // DAYS_PER_MONTH_APPROX}mo ago"
        else:
            return f"{days_ago // DAYS_PER_YEAR}y ago"
    except (ValueError, AttributeError):
        return "unknown"


def truncate_description(description: Optional[str], max_length: Optional[int] = None) -> str:
    """Truncate description with ellipsis if too long.

    Args:
        description: Repository description
        max_length: Maximum length before truncation (defaults to TABLE_CONFIG value)

    Returns:
        Truncated description string
    """
    if not description:
        return "No description"

    if max_length is None:
        max_length = TABLE_CONFIG["description_max_length"]

    if len(description) > max_length:
        return description[: max_length - 3] + "..."
    return description


def create_repository_table(
    repos: List[Dict[str, Any]],
    title: str = "Repositories",
    include_rank: bool = False,
    include_activity: bool = False,
    console: Any = None,
) -> None:
    """Create and display a formatted repository table.

    Args:
        repos: List of repository dictionaries from GitHub API
        title: Table title
        include_rank: Whether to include rank column
        include_activity: Whether to show activity summary instead of separate columns
        console: Console instance for printing
    """
    if not console:
        raise ValueError("Console instance required")

    if not repos:
        console.print("[warning]No repositories found.[/]")
        return

    # Rich table
    if Table:
        table = Table(
            title=title,
            box=box.ROUNDED,
            show_header=True,
            header_style="bold cyan",
        )

        # Add columns based on options
        if include_rank:
            table.add_column("Rank", justify="right", style="dim", width=4)

        table.add_column("Repository", style="cyan", no_wrap=True)
        table.add_column("Description", style="dim")

        if include_activity:
            table.add_column("Activity", justify="right", style="success")
        else:
            table.add_column("Stars", justify="right", style="warning")
            table.add_column("Forks", justify="right", style="success")

        table.add_column("Updated", justify="right", style="dim")

        # Add rows
        for i, repo in enumerate(repos, 1):
            full_name = repo.get("full_name", "unknown/repo")
            max_desc_length = (
                TABLE_CONFIG["description_max_length_with_rank"]
                if include_rank
                else TABLE_CONFIG["description_max_length"]
            )
            description = truncate_description(repo.get("description"), max_length=max_desc_length)

            # Format updated date
            updated_at = repo.get("updated_at", "")
            updated_str = format_relative_date(updated_at)

            row_data = []

            if include_rank:
                row_data.append(f"#{i}")

            row_data.append(full_name)
            row_data.append(description)

            if include_activity:
                # Activity summary
                stars = repo.get("stargazers_count", 0)
                forks = repo.get("forks_count", 0)
                issues = repo.get("open_issues_count", 0)
                activity = f"⭐{stars} 🍴{forks} 📋{issues}"
                row_data.append(activity)
            else:
                # Separate columns for stars and forks
                stars = str(repo.get("stargazers_count", 0))
                forks = str(repo.get("forks_count", 0))
                row_data.extend([stars, forks])

            row_data.append(updated_str)
            table.add_row(*row_data)

        console.print(table)
    else:
        # Fallback for environments without rich
        console.print(f"{title}:\n")
        for i, repo in enumerate(repos, 1):
            full_name = repo.get("full_name", "unknown/repo")
            description = repo.get("description") or "No description"
            stars = repo.get("stargazers_count", 0)

            if include_rank:
                console.print(f"#{i}. {full_name}")
            else:
                console.print(f"{i}. {full_name}")

            console.print(f"   {description}")
            console.print(f"   ⭐ {stars} stars\n")


__all__ = [
    "format_relative_date",
    "truncate_description",
    "create_repository_table",
]
