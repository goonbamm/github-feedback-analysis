"""Command line interface for the GitHub feedback toolkit."""

from __future__ import annotations

import os
from pathlib import Path

import typer

from ..core.console import Console

# Import CLI command modules
from . import config as cli_config
from . import feedback as cli_feedback
from . import repos as cli_repos

# Create Typer app instances
app = typer.Typer(help="Analyze GitHub repositories and generate feedback reports.")
config_app = typer.Typer(help="Manage configuration settings")
app.add_typer(config_app, name="config")

console = Console()


# ============================================================================
# Main Commands
# ============================================================================

@app.command()
def init(
    pat: str = typer.Option(
        None,
        "--pat",
        help="GitHub Personal Access Token (requires 'repo' scope for private repos)",
        hide_input=True,
    ),
    months: int = typer.Option(12, "--months", help="Default analysis window in months"),
    enterprise_host: str = typer.Option(
        None,
        "--enterprise-host",
        help=(
            "Base URL of your GitHub Enterprise host (e.g. https://github.example.com). "
            "When provided, API, GraphQL, and web URLs are derived automatically."
        ),
    ),
    llm_endpoint: str = typer.Option(
        None,
        "--llm-endpoint",
        help="LLM endpoint URL (e.g. https://api.openai.com/v1/chat/completions)",
    ),
    llm_model: str = typer.Option(
        None,
        "--llm-model",
        help="Model identifier for the LLM",
    ),
    test_connection: bool = typer.Option(
        True,
        "--test/--no-test",
        help="Test LLM connection after configuration",
    ),
) -> None:
    """Initialize configuration and store credentials securely."""
    cli_config.init(pat, months, enterprise_host, llm_endpoint, llm_model, test_connection)


@app.command()
def feedback(
    repo: str = typer.Option(
        None,
        "--repo",
        "-r",
        help="Repository in owner/name format (e.g. microsoft/vscode)",
    ),
    output_dir: Path = typer.Option(
        Path("reports"),
        "--output",
        "-o",
        help="Output directory for reports",
    ),
    interactive: bool = typer.Option(
        False,
        "--interactive",
        "-i",
        help="Interactively select repository from suggestions",
    ),
    year_in_review: bool = typer.Option(
        False,
        "--year-in-review",
        "-y",
        help="Analyze all repositories you contributed to this year and generate a comprehensive annual report",
    ),
    year: int = typer.Option(
        None,
        "--year",
        help="Specific year for year-in-review (default: current year)",
    ),
) -> None:
    """Analyze repository activity and generate detailed reports with PR feedback."""
    cli_feedback.feedback(repo, output_dir, interactive, year_in_review, year)


@app.command(name="list-repos")
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
    org: str = typer.Option(
        None,
        "--org",
        "-o",
        help="Filter by organization name",
    ),
) -> None:
    """List repositories accessible to the authenticated user."""
    cli_repos.list_repos(sort, limit, org)


@app.command(name="suggest-repos")
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
    """Suggest repositories for analysis based on activity and recency."""
    cli_repos.suggest_repos(limit, days, sort)


@app.command(name="clear-cache")
def clear_cache() -> None:
    """Clear the API response cache."""
    cli_repos.clear_cache()


# ============================================================================
# Config Commands
# ============================================================================

@config_app.command("show")
def show_config() -> None:
    """Display current configuration settings."""
    cli_config.show_config()


@config_app.command("set")
def config_set(
    key: str = typer.Argument(..., help="Configuration key in dot notation (e.g. llm.model)"),
    value: str = typer.Argument(..., help="Value to set"),
) -> None:
    """Set a configuration value."""
    cli_config.config_set(key, value)


@config_app.command("get")
def config_get(
    key: str = typer.Argument(..., help="Configuration key in dot notation (e.g. llm.model)"),
) -> None:
    """Get a configuration value."""
    cli_config.config_get(key)


@config_app.command("hosts")
def config_hosts(
    action: str = typer.Argument(
        ...,
        help="Action to perform: list, add, or remove"
    ),
    host: str = typer.Argument(
        None,
        help="Host URL (required for add/remove actions)"
    ),
) -> None:
    """Manage custom enterprise hosts."""
    cli_config.config_hosts(action, host)


# ============================================================================
# Deprecated Commands (for backward compatibility)
# ============================================================================

@app.command(name="show-config", hidden=True, deprecated=True)
def show_config_deprecated() -> None:
    """Display current configuration settings (deprecated: use 'gfa config show')."""
    cli_config.show_config_deprecated()


# ============================================================================
# App Callback
# ============================================================================

@app.callback()
def main_callback(
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose output for debugging",
    ),
    quiet: bool = typer.Option(
        False,
        "--quiet",
        "-q",
        help="Suppress non-essential output",
    ),
    no_color: bool = typer.Option(
        False,
        "--no-color",
        help="Disable colored output",
    ),
) -> None:
    """CLI entry-point callback for shared initialisation."""
    from .christmas_theme import is_christmas_season, get_christmas_banner

    # Set console modes
    console.set_verbose(verbose)
    console.set_quiet(quiet)

    if no_color:
        os.environ["NO_COLOR"] = "1"

    # Display Christmas decorations if in season (Nov 1 - Dec 31) and not in quiet mode
    disable_theme = os.getenv("GHF_NO_THEME", "").lower() in ("1", "true", "yes")
    if is_christmas_season() and not disable_theme and not quiet:
        console.print(get_christmas_banner())
