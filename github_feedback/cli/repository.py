"""Repository selection and management utilities for CLI."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional, Tuple

import requests
import typer

try:  # pragma: no cover - optional rich dependency
    from rich import box
    from rich.table import Table
except ModuleNotFoundError:  # pragma: no cover - fallback when rich is missing
    Table = None
    box = None

from .collector import Collector
from ..core.console import Console
from ..core.constants import (
    ERROR_MESSAGES,
    INFO_MESSAGES,
    SPINNERS,
    TABLE_CONFIG,
)
from ..core.utils import validate_repo_format

console = Console()


def select_repository_interactive(collector: Collector) -> Optional[str]:
    """Interactively select a repository from suggestions.

    Args:
        collector: Collector instance for fetching repositories

    Returns:
        Selected repository in owner/repo format, or None if cancelled
    """
    console.print(f"[info]{INFO_MESSAGES['fetching_repos']}[/]")

    with console.status(f"[accent]{INFO_MESSAGES['analyzing_repos']}", spinner=SPINNERS['bouncing']):
        try:
            suggestions = collector.suggest_repositories(limit=10, min_activity_days=90)
        except KeyboardInterrupt:
            raise
        except (requests.RequestException, ValueError) as exc:
            console.print_error(exc, "Error fetching suggestions:")
            return None

    if not suggestions:
        console.print(f"[warning]{ERROR_MESSAGES['no_suggestions']}[/]")
        console.print(f"[info]{INFO_MESSAGES['try_manual_repo']}[/]")
        return None

    # Display suggestions in a table
    if Table:
        console.print()
        table = Table(
            title="Suggested Repositories",
            box=getattr(box, TABLE_CONFIG['box_style']),
            show_header=True,
            header_style=TABLE_CONFIG['header_style'],
        )

        table.add_column("#", justify="right", style=TABLE_CONFIG['index_style'], width=TABLE_CONFIG['index_width'])
        table.add_column("Repository", style="cyan", no_wrap=True)
        table.add_column("Description", style="dim")
        table.add_column("Your Commits", justify="right", style="bold green")
        table.add_column("Activity", justify="right", style=TABLE_CONFIG['activity_style'])

        for i, repo in enumerate(suggestions, 1):
            full_name = repo.get("full_name", "unknown/repo")
            description = repo.get("description") or "No description"
            max_len = TABLE_CONFIG['description_max_length']
            if len(description) > max_len:
                description = description[:max_len-3] + "..."

            stars = repo.get("stargazers_count", 0)
            forks = repo.get("forks_count", 0)
            user_commits = repo.get("_user_commits", 0)

            # Highlight repos with user contributions
            commits_display = f"✓ {user_commits}" if user_commits > 0 else "-"
            activity = f"⭐{stars} 🍴{forks}"

            table.add_row(str(i), full_name, description, commits_display, activity)

        console.print(table)
    else:
        # Fallback if rich is not available
        console.print("\nSuggested Repositories:\n")
        for i, repo in enumerate(suggestions, 1):
            full_name = repo.get("full_name", "unknown/repo")
            description = repo.get("description") or "No description"
            stars = repo.get("stargazers_count", 0)
            user_commits = repo.get("_user_commits", 0)
            commit_info = f" [YOUR COMMITS: {user_commits}]" if user_commits > 0 else ""
            console.print(f"{i}. {full_name} - {description} (⭐ {stars}){commit_info}")
    console.print()
    console.print("[info]Select a repository by number (1-{}) or enter owner/repo format[/]".format(len(suggestions)))
    console.print("[info]Press Ctrl+C or enter 'q' to quit[/]")
    console.print()

    # Prompt for selection
    while True:
        try:
            selection = typer.prompt("Repository", default="").strip()

            if not selection or selection.lower() == 'q':
                return None

            # Check if it's a number selection
            if selection.isdigit():
                index = int(selection) - 1
                if 0 <= index < len(suggestions):
                    selected_repo = suggestions[index].get("full_name")
                    console.print(f"[success]Selected:[/] {selected_repo}")
                    return selected_repo
                else:
                    console.print(f"[danger]Invalid selection.[/] Please enter a number between 1 and {len(suggestions)}")
                    continue

            # Otherwise, treat it as owner/repo format
            try:
                validate_repo_format(selection)
                console.print(f"[success]Selected:[/] {selection}")
                return selection
            except ValueError as exc:
                console.print(f"[danger]Invalid format:[/] {exc}")
                console.print("[info]Enter a number (1-{}) or owner/repo format[/]".format(len(suggestions)))
                continue

        except (typer.Abort, KeyboardInterrupt, EOFError):
            console.print("\n[warning]Selection cancelled.[/]")
            return None


def load_default_hosts() -> list[str]:
    """Load default hosts from config file.

    Returns:
        List of default host examples
    """
    # Default fallback hosts if config file is not found
    fallback_hosts = [
        "github.com (Default)",
        "github.company.com",
        "github.enterprise.local",
        "ghe.example.com",
    ]

    try:
        # Get the path to hosts.config.json in the .config directory
        config_path = Path(__file__).parent.parent / ".config" / "hosts.config.json"

        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
                return config_data.get("default_hosts", fallback_hosts)
        else:
            return fallback_hosts
    except Exception:
        # If any error occurs, use fallback
        return fallback_hosts


def select_enterprise_host_interactive(custom_hosts: list[str]) -> Optional[Tuple[str, bool]]:
    """Interactive enterprise host selection with preset and custom options.

    Args:
        custom_hosts: List of user-configured custom enterprise hosts

    Returns:
        Tuple of (selected_host, should_save) or None if cancelled
        - selected_host: The enterprise host URL (empty string for github.com)
        - should_save: Whether to save this host to custom list
    """
    # Load default example hosts from config
    default_hosts = load_default_hosts()

    console.print("\n[accent]Select GitHub Enterprise Host:[/]")
    console.print("[info]Choose from the list or enter a custom URL[/]\n")

    # Display options
    menu_option = 1

    # Show default github.com option
    console.print(f"  {menu_option}. [success]github.com[/] (Default)")
    github_com_idx = menu_option
    menu_option += 1

    # Show example hosts
    if len(default_hosts) > 1:
        console.print("\n[dim]Example Enterprise Hosts:[/]")
        for host in default_hosts[1:]:
            console.print(f"  {menu_option}. {host}")
            menu_option += 1

    # Show custom hosts if any
    if custom_hosts:
        console.print("\n[dim]Your Saved Hosts:[/]")
        custom_start_idx = menu_option
        for host in custom_hosts:
            console.print(f"  {menu_option}. [accent]{host}[/]")
            menu_option += 1
    else:
        custom_start_idx = menu_option

    console.print(f"\n[info]Or enter a custom host URL (e.g., https://github.example.com)[/]")

    while True:
        try:
            selection = typer.prompt("\nEnter number or custom URL", default="1").strip()

            # Check if it's a number selection
            if selection.isdigit():
                selection_num = int(selection)

                # GitHub.com selection
                if selection_num == github_com_idx:
                    console.print("[success]Selected:[/] github.com (Default)")
                    return ("", False)

                # Example host selection
                elif github_com_idx < selection_num < custom_start_idx:
                    example_idx = selection_num - 2  # -2 because we skip "github.com (Default)" in list
                    if 0 <= example_idx < len(default_hosts) - 1:
                        selected = default_hosts[example_idx + 1]
                        console.print(f"[info]Selected example:[/] {selected}")

                        # Ask if user wants to save this
                        save = typer.confirm("Save this host to your custom list?", default=True)
                        return (selected, save)

                # Custom host selection
                elif custom_hosts and custom_start_idx <= selection_num < custom_start_idx + len(custom_hosts):
                    custom_idx = selection_num - custom_start_idx
                    selected = custom_hosts[custom_idx]
                    console.print(f"[success]Selected:[/] {selected}")
                    return (selected, False)  # Already saved

                else:
                    console.print(f"[danger]Invalid selection.[/] Please enter a number between 1 and {menu_option - 1}")
                    continue

            # Custom URL input
            else:
                console.print(f"[info]Custom host:[/] {selection}")

                # Ask if user wants to save this
                save = typer.confirm("Save this host to your custom list for future use?", default=True)
                return (selection, save)

        except (typer.Abort, KeyboardInterrupt, EOFError):
            console.print("\n[warning]Selection cancelled.[/]")
            return None


def get_authenticated_user(collector: Collector) -> str:
    """Authenticate and get the current GitHub user.

    Args:
        collector: Collector instance for authentication

    Returns:
        GitHub username of authenticated user

    Raises:
        typer.Exit: If authentication fails
    """
    console.print()
    console.rule("Phase 0: Authentication")
    with console.status("[accent]Retrieving authenticated user...", spinner="dots"):
        try:
            author = collector.get_authenticated_user()
            console.print(f"[success]✓ Authenticated as: {author}[/]")
            return author
        except (ValueError, PermissionError) as exc:
            console.print(f"[error]Failed to get authenticated user: {exc}[/]")
            raise typer.Exit(code=1) from exc
