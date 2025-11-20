"""Command line interface for the GitHub feedback toolkit.

This is the main CLI entry point that orchestrates all commands.
The implementation has been refactored into modular components:
- commands/    - Command handlers
- workflows/   - Business logic workflows
- ui/          - User interface components
- utils/       - Utility functions
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable, Optional

import typer

from ..analyzer import Analyzer
from ..collector import Collector
from ..console import Console
from ..llm import LLMClient
from ..reporter import Reporter
from ..reviewer import Reviewer
from .utils import config_utils
from .utils.config_utils import load_config as _load_config
from .utils.config_utils import print_config_summary as _print_config_summary
from .utils.metrics_utils import persist_metrics
from .ui.display import render_metrics as _render_metrics
from .workflows import feedback_workflow
from .workflows.feedback_workflow import (
    _collect_detailed_feedback,
    _generate_integrated_full_report,
)

__all__ = [
    "app",
    "init",
    "feedback",
    "review",
    "_collect_detailed_feedback",
    "_generate_integrated_full_report",
    "_load_config",
    "_print_config_summary",
    "Collector",
    "Analyzer",
    "LLMClient",
    "Reporter",
    "Reviewer",
    "persist_metrics",
    "_render_metrics",
]

# Keep command modules in sync with patchable helpers
config_utils.load_config = _load_config
config_utils.print_config_summary = _print_config_summary
feedback_workflow.persist_metrics = persist_metrics
feedback_workflow.render_metrics = _render_metrics

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
    from ..christmas_theme import is_christmas_season, get_christmas_banner

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
from .commands import init_cmd, config_cmd, repos_cmd, cache_cmd, feedback_cmd

# Ensure command modules use patchable helpers
init_cmd.print_config_summary = _print_config_summary
feedback_cmd.load_config = _load_config

# Register commands
init_cmd.register_command(app)
config_cmd.register_commands(app)
repos_cmd.register_commands(app)
cache_cmd.register_command(app)
feedback_cmd.register_command(app)


def init(*args, **kwargs):  # type: ignore[override]
    """Compatibility wrapper for the init command used in tests."""
    return init_cmd.init(app, *args, **kwargs)


def feedback(*args, **kwargs):  # type: ignore[override]
    """Compatibility wrapper for the feedback command used in tests."""
    return feedback_cmd.feedback(*args, **kwargs)


def _resolve_review_numbers(
    collector: Collector, repo: str, number: Optional[int], state: str
) -> Iterable[int]:
    """Resolve pull request numbers to review based on CLI options."""
    if number is not None:
        return [number]

    author = collector.get_authenticated_user()
    numbers = collector.list_authored_pull_requests(repo=repo, author=author, state=state)
    return sorted(set(numbers))


def review(repo: str, number: Optional[int] = None, state: str = "open") -> None:
    """Review pull requests authored by the authenticated user.

    Args:
        repo: Repository in owner/name format.
        number: Specific PR number to review. If omitted, authored PRs are listed.
        state: Filter for authored PRs when number is not provided.
    """
    config = _load_config()
    collector = Collector(config)
    llm_client = LLMClient(config.llm.endpoint, config.llm.model)
    reviewer = Reviewer(collector=collector, llm=llm_client, output_dir=Path("reviews"))

    for pr_number in _resolve_review_numbers(collector, repo, number, state):
        reviewer.review_pull_request(repo, pr_number)

    console.print(f"[info]Review artefacts stored under: {Path('reviews').resolve()}")


# Deprecated command (for backward compatibility)
@app.command(name="show-config", hidden=True, deprecated=True)
def show_config_deprecated() -> None:
    """Display current configuration settings (deprecated: use 'gfa config show')."""
    from .utils.config_utils import print_config_summary

    console.print("[warning]Note:[/] 'gfa show-config' is deprecated. Use 'gfa config show' instead.")
    console.print()
    print_config_summary()
