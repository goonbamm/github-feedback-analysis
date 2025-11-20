"""Feedback analysis command for GitHub Feedback Analysis CLI.

This module contains the main feedback command which analyzes repository
activity and generates detailed reports with PR feedback.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

import requests
import typer

try:
    from rich.table import Table
    from rich import box
except ModuleNotFoundError:
    Table = None
    box = None

from ...collector import Collector
from ...console import Console
from ...constants import (
    DAYS_PER_MONTH_APPROX,
    ERROR_MESSAGES,
    INFO_MESSAGES,
    SPINNERS,
    TABLE_CONFIG,
)
from ...models import AnalysisFilters
from ...utils import validate_repo_format
from ..utils.config_utils import load_config
from ..utils.output_utils import resolve_output_dir
from ..workflows.feedback_workflow import (
    _collect_detailed_feedback,
    _collect_personal_activity,
    _collect_yearend_data,
    _compute_and_display_metrics,
    _generate_final_report,
    _generate_reports_and_artifacts,
    _get_authenticated_user,
    _run_pr_reviews,
)
from ..workflows.year_review_workflow import _run_year_in_review_analysis

console = Console()


def _display_final_summary(
    author: str,
    repo_input: str,
    pr_results: list,
    integrated_report_path: Optional[Path],
    artifacts: list,
) -> None:
    """Display final summary of the analysis.

    Args:
        author: GitHub username
        repo_input: Repository name
        pr_results: PR review results
        integrated_report_path: Path to integrated report
        artifacts: List of generated artifacts
    """
    console.print()
    console.rule("Summary")
    console.print(f"[success]✓ Complete analysis for {author}[/]")
    console.print(f"[success]✓ Repository:[/] {repo_input}")
    console.print(f"[success]✓ PRs reviewed:[/] {len(pr_results)}")
    console.print()

    if integrated_report_path:
        console.print("[info]📊 Final Report:[/]")
        console.print(f"  • [accent]{integrated_report_path}[/]")
        console.print()
        console.print("[info]💡 Next steps:[/]")
        console.print(f"  • View the full report: [accent]cat {integrated_report_path}[/]")
        console.print("  • View individual PR reviews in: [accent]reports/reviews/[/]")
    else:
        console.print("[warning]No integrated report was generated.[/]")
        console.print("[info]Individual artifacts:[/]")
        for label, path in artifacts:
            if "Internal report" not in label:
                console.print(f"  • {label}: [accent]{path}[/]")


def _select_repository_interactive(collector: Collector) -> Optional[str]:
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


def feedback(
    repo: Optional[str] = typer.Option(
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
    year: Optional[int] = typer.Option(
        None,
        "--year",
        help="Specific year for year-in-review (default: current year)",
    ),
) -> None:
    """Analyze repository activity and generate detailed reports with PR feedback.

    This command collects commits, PRs, reviews, and issues from a GitHub
    repository, analyzes all PRs authored by you, then generates comprehensive
    reports with insights and recommendations.

    With --year-in-review, analyzes all repositories you contributed to during
    the specified year and generates a comprehensive annual summary report.

    Examples:
        gfa feedback --repo torvalds/linux
        gfa feedback --repo myorg/myrepo --output custom_reports/
        gfa feedback --interactive
        gfa feedback --year-in-review
        gfa feedback --year-in-review --year 2024
    """
    # Initialize configuration and components
    config = load_config()

    # Handle year-in-review mode
    if year_in_review:
        output_dir_resolved = resolve_output_dir(output_dir)
        _run_year_in_review_analysis(config, output_dir_resolved, year)
        return

    months = config.defaults.months
    filters = AnalysisFilters(
        include_branches=[],
        exclude_branches=[],
        include_paths=[],
        exclude_paths=[],
        include_languages=[],
        exclude_bots=True,
    )

    try:
        collector = Collector(config)
    except ValueError as exc:
        console.print_error(exc)
        console.print("[info]Hint:[/] Check your GitHub token with [accent]gfa show-config[/]")
        raise typer.Exit(code=1) from exc

    # Select repository
    if interactive or repo is None:
        repo_input = _select_repository_interactive(collector)
        if not repo_input:
            console.print("[warning]No repository selected.[/]")
            raise typer.Exit(code=0)
    else:
        repo_input = repo.strip()

    # Validate repository format
    try:
        validate_repo_format(repo_input)
    except ValueError as exc:
        console.print_validation_error(str(exc))
        console.print("[info]Example:[/] [accent]gfa feedback --repo torvalds/linux[/]")
        raise typer.Exit(code=1) from exc

    # Initialize analyzer and reporter
    from ...analyzer import Analyzer
    from ...reporter import Reporter
    from ...llm import LLMClient

    analyzer = Analyzer(web_base_url=config.server.web_url)
    output_dir_resolved = resolve_output_dir(output_dir)

    # Create LLM client for reporter (used for generating summary quotes)
    llm_client = LLMClient(
        endpoint=config.llm.endpoint,
        model=config.llm.model,
        timeout=config.llm.timeout,
        web_url=config.server.web_url,
    )
    reporter = Reporter(output_dir=output_dir_resolved, llm_client=llm_client, web_url=config.server.web_url)

    # Execute analysis workflow
    author = _get_authenticated_user(collector)
    collection = _collect_personal_activity(collector, repo_input, months, filters, author)

    # Collect detailed feedback
    console.print()
    console.rule("Phase 2: Detailed Feedback Analysis")
    since = datetime.now(timezone.utc) - timedelta(days=DAYS_PER_MONTH_APPROX * max(months, 1))
    detailed_feedback_snapshot = _collect_detailed_feedback(
        collector, analyzer, config, repo_input, since, filters, author
    )

    # Collect year-end data
    console.print()
    console.rule("Phase 2.5: Year-End Review Data")
    monthly_trends_data, tech_stack_data, collaboration_data = _collect_yearend_data(
        collector, repo_input, since, filters, author
    )

    # Compute metrics and display
    metrics = _compute_and_display_metrics(
        analyzer, collection, detailed_feedback_snapshot,
        monthly_trends_data, tech_stack_data, collaboration_data
    )

    # Generate reports
    artifacts, brief_content = _generate_reports_and_artifacts(metrics, reporter, output_dir_resolved)

    # Run PR reviews
    feedback_report_path, pr_results = _run_pr_reviews(config, repo_input, output_dir_resolved)

    # Generate final integrated report
    integrated_report_path = _generate_final_report(
        output_dir_resolved, repo_input, brief_content, feedback_report_path
    )

    # Display summary
    _display_final_summary(author, repo_input, pr_results, integrated_report_path, artifacts)


def register_command(app: typer.Typer) -> None:
    """Register the feedback command with the CLI app."""
    app.command()(feedback)
