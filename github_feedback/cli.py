"""Command line interface for the GitHub feedback toolkit.

This is the main CLI entry point that orchestrates all commands.
The implementation has been refactored into modular components:
- cli/commands/    - Command handlers
- cli/workflows/   - Business logic workflows
- cli/ui/          - User interface components
- cli/utils/       - Utility functions
"""

from __future__ import annotations

import os

import typer

from .console import Console


# Initialize main CLI application
app = typer.Typer(help="Analyze GitHub repositories and generate feedback reports.")
console = Console()


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


# Register all command modules
from .cli.commands import init_cmd, config_cmd, repos_cmd, cache_cmd, feedback_cmd

# Register commands
init_cmd.register_command(app)
config_cmd.register_commands(app)
repos_cmd.register_commands(app)
cache_cmd.register_command(app)
feedback_cmd.register_command(app)


# Deprecated command (for backward compatibility)
@app.command(name="show-config", hidden=True, deprecated=True)
def show_config_deprecated() -> None:
    """Display current configuration settings (deprecated: use 'gfa config show')."""
    from .cli.utils.config_utils import print_config_summary

    console.print("[warning]Note:[/] 'gfa show-config' is deprecated. Use 'gfa config show' instead.")
    console.print()
    print_config_summary()
