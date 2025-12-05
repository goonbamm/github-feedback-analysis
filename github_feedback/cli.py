"""Command line interface for the GitHub feedback toolkit."""

from __future__ import annotations

import json
import logging
import os
import sys
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Annotated, Any, Callable, Dict, List, Optional, Tuple

import requests
import typer

try:  # pragma: no cover - optional rich dependency
    from rich import box
    from rich.align import Align
    from rich.columns import Columns
    from rich.console import Group
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeRemainingColumn
    from rich.rule import Rule
    from rich.table import Table
    from rich.text import Text
except ModuleNotFoundError:  # pragma: no cover - fallback when rich is missing
    Align = None
    Columns = None
    Group = None
    Panel = None
    Progress = None
    Rule = None
    Table = None
    Text = None
    box = None

from .analyzer import Analyzer
from .collector import Collector
from .config import Config
from .console import Console
from .constants import (
    COLLECTION_LIMITS,
    DAYS_PER_MONTH_APPROX,
    DAYS_PER_YEAR,
    ERROR_MESSAGES,
    INFO_MESSAGES,
    PARALLEL_CONFIG,
    SPINNERS,
    SUCCESS_MESSAGES,
    TABLE_CONFIG,
    TaskType,
)
from .exceptions import (
    CollectionError,
    CollectionTimeoutError,
    LLMAnalysisError,
    LLMTimeoutError,
)
from .llm import LLMClient
from .models import (
    AnalysisFilters,
    AnalysisStatus,
    DetailedFeedbackSnapshot,
    MetricSnapshot,
)
from .reporter import Reporter
from .repository_display import create_repository_table, format_relative_date
from .review_reporter import ReviewReporter
from .reviewer import Reviewer
from .utils import validate_pat_format, validate_url, validate_repo_format, validate_months

# Import refactored CLI modules
from . import cli_helpers
from . import cli_repository
from . import cli_metrics
from . import cli_data_collection
from . import cli_yearinreview
from . import cli_report_integration

app = typer.Typer(help="Analyze GitHub repositories and generate feedback reports.")
config_app = typer.Typer(help="Manage configuration settings")
app.add_typer(config_app, name="config")

console = Console()
logger = logging.getLogger(__name__)


@app.command()
def init(
    pat: Optional[str] = typer.Option(
        None,
        "--pat",
        help="GitHub Personal Access Token (requires 'repo' scope for private repos)",
        hide_input=True,
    ),
    months: int = typer.Option(12, "--months", help="Default analysis window in months"),
    enterprise_host: Optional[str] = typer.Option(
        None,
        "--enterprise-host",
        help=(
            "Base URL of your GitHub Enterprise host (e.g. https://github.example.com). "
            "When provided, API, GraphQL, and web URLs are derived automatically."
        ),
    ),
    llm_endpoint: Optional[str] = typer.Option(
        None,
        "--llm-endpoint",
        help="LLM endpoint URL (e.g. https://api.openai.com/v1/chat/completions)",
    ),
    llm_model: Optional[str] = typer.Option(
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
    """Initialize configuration and store credentials securely.

    This command sets up your GitHub access token, LLM endpoint, and other
    configuration options. Run this once before using other commands.

    Interactive mode: Run without options to be prompted for each value.
    Non-interactive mode: Provide all required options for scripting.
    """
    from ._cli.commands.init_command import InitCommand

    command = InitCommand(console)
    command.execute(
        pat=pat,
        months=months,
        enterprise_host=enterprise_host,
        llm_endpoint=llm_endpoint,
        llm_model=llm_model,
        test_connection=test_connection,
    )


def _generate_artifacts(
    metrics: MetricSnapshot,
    reporter: Reporter,
    output_dir: Path,
    metrics_payload: dict,
    save_intermediate_report: bool = True,
) -> tuple[List[tuple[str, Path]], Optional[str]]:
    """Generate all report artifacts and return brief report content in memory.

    Args:
        metrics: Metrics snapshot to generate reports from
        reporter: Reporter instance
        output_dir: Output directory for artifacts
        metrics_payload: Metrics data for serialization
        save_intermediate_report: If True, generates brief report content in memory for integration.
                                  If False, skips brief report generation.

    Returns:
        Tuple of (artifacts, brief_content):
            - artifacts: List of (label, path) tuples for generated artifacts
            - brief_content: Markdown content for brief report (None if not generated)
    """
    artifacts = []

    # Save metrics
    metrics_path = cli_metrics.persist_metrics(output_dir=output_dir, metrics_data=metrics_payload)
    artifacts.append(("Metrics snapshot", metrics_path))

    # Generate markdown report content in memory (no _internal folder needed)
    brief_content = None
    if save_intermediate_report:
        # Generate content in memory without creating files
        brief_content = reporter.generate_markdown_content(metrics)
    else:
        markdown_path = reporter.generate_markdown(metrics)
        artifacts.append(("Markdown report", markdown_path))

    return artifacts, brief_content


def _run_feedback_analysis(
    config: Config,
    repo_input: str,
    output_dir: Path,
) -> tuple[Path | None, list[tuple[int, Path, Path, Path]]]:
    """Run feedback analysis for all PRs authored by the authenticated user.

    Args:
        config: Configuration object
        repo_input: Repository name in owner/repo format
        output_dir: Output directory for review artifacts

    Returns:
        Tuple of (integrated_report_path, pr_results)
        where pr_results is a list of (pr_number, artefact_path, summary_path, markdown_path)
    """
    try:
        collector = Collector(config)
    except ValueError as exc:
        console.print_error(exc)
        return None, []

    llm_client = LLMClient(
        endpoint=config.llm.endpoint,
        model=config.llm.model,
        timeout=config.llm.timeout,
        max_files_in_prompt=config.llm.max_files_in_prompt,
        max_files_with_patch_snippets=config.llm.max_files_with_patch_snippets,
        web_url=config.server.web_url,
    )

    reviews_dir = output_dir / "reviews"
    reviewer = Reviewer(collector=collector, llm=llm_client, output_dir=reviews_dir)

    # Get authenticated user
    with console.status("[accent]Retrieving authenticated user...", spinner="dots"):
        try:
            author = collector.get_authenticated_user()
        except (ValueError, PermissionError) as exc:
            console.print(f"[error]Failed to get authenticated user: {exc}[/]")
            return None, []

    # Find user's PRs
    with console.status("[accent]Finding your pull requests...", spinner="dots"):
        numbers = collector.list_authored_pull_requests(
            repo=repo_input,
            author=author,
            state="all",
        )

    if not numbers:
        console.print(
            f"[warning]No pull requests found authored by '{author}' in {repo_input}.[/]"
        )
        return None, []

    pr_numbers = sorted(set(numbers))
    total_prs = len(pr_numbers)

    # Generate PR reviews in parallel
    console.print(f"[info]Analyzing {total_prs} PRs in parallel...[/]")

    review_tasks = {
        f"pr_{pr_number}": (
            reviewer.review_pull_request,
            (repo_input, pr_number),
            f"PR #{pr_number}"
        )
        for pr_number in pr_numbers
    }

    review_results = cli_helpers.run_parallel_tasks(
        review_tasks,
        PARALLEL_CONFIG['max_workers_pr_review'],
        PARALLEL_CONFIG['pr_review_timeout'],
        task_type="analysis"
    )

    # Collect results
    results = []
    for pr_number in pr_numbers:
        key = f"pr_{pr_number}"
        if key in review_results and review_results[key] is not None:
            artefact_path, summary_path, markdown_path = review_results[key]
            results.append((pr_number, artefact_path, summary_path, markdown_path))
        else:
            console.print(f"[warning]⚠ PR #{pr_number} review failed or timed out[/]", style="warning")

    # Generate integrated report
    output_dir_resolved = cli_helpers.resolve_output_dir(output_dir)
    reviews_dir = output_dir_resolved / "reviews"
    review_reporter = ReviewReporter(
        output_dir=reviews_dir,
        llm=llm_client,
    )

    try:
        with console.status("[accent]Creating integrated report...", spinner="dots"):
            report_path = review_reporter.create_integrated_report(repo_input)
    except ValueError as exc:
        console.print(f"[warning]{exc}[/]")
        return None, results

    return report_path, results


def _generate_integrated_full_report(
    output_dir: Path,
    repo_name: str,
    brief_content: str,
    feedback_report_path: Path,
) -> Path:
    """Generate an improved integrated report with better UX.

    Args:
        output_dir: Output directory for the integrated report
        repo_name: Repository name in owner/repo format
        brief_content: Brief report markdown content (from memory)
        feedback_report_path: Path to the feedback integrated report markdown file

    Returns:
        Path to the generated integrated report

    Raises:
        RuntimeError: If file operations fail
    """
    return cli_report_integration.generate_integrated_full_report(
        output_dir=output_dir,
        repo_name=repo_name,
        brief_content=brief_content,
        feedback_report_path=feedback_report_path,
    )


def _generate_reports_and_artifacts(
    metrics: MetricSnapshot,
    reporter: Reporter,
    output_dir_resolved: Path,
) -> tuple[List[tuple[str, Path]], Optional[str]]:
    """Generate report artifacts.

    Args:
        metrics: Metrics snapshot
        reporter: Reporter instance
        output_dir_resolved: Output directory path

    Returns:
        Tuple of (artifacts, brief_content)
    """
    console.print()
    console.rule("Phase 4: Report Generation")
    metrics_payload = cli_metrics.prepare_metrics_payload(metrics)
    artifacts, brief_content = _generate_artifacts(
        metrics, reporter, output_dir_resolved, metrics_payload, save_intermediate_report=True
    )
    return artifacts, brief_content


def _run_pr_reviews(
    config: Config,
    repo_input: str,
    output_dir_resolved: Path,
) -> tuple[Path | None, list[tuple[int, Path, Path, Path]]]:
    """Run PR review analysis.

    Args:
        config: Configuration object
        repo_input: Repository name
        output_dir_resolved: Output directory

    Returns:
        Tuple of (feedback_report_path, pr_results)
    """
    console.print()
    console.rule("Phase 6: PR Review Analysis")
    console.print("[accent]Analyzing all your PRs with AI-powered reviews...[/]")
    feedback_report_path, pr_results = _run_feedback_analysis(
        config=config,
        repo_input=repo_input,
        output_dir=output_dir_resolved,
    )

    if feedback_report_path:
        console.print(f"[success]✓ PR review analysis complete[/]")
    else:
        console.print("[warning]⚠ PR review analysis skipped or failed[/]")

    return feedback_report_path, pr_results


def _generate_final_report(
    output_dir_resolved: Path,
    repo_input: str,
    brief_content: Optional[str],
    feedback_report_path: Optional[Path],
) -> Optional[Path]:
    """Generate integrated full report.

    Args:
        output_dir_resolved: Output directory
        repo_input: Repository name
        brief_content: Brief report content
        feedback_report_path: Path to feedback report

    Returns:
        Path to integrated report or None if not generated
    """
    console.print()
    console.rule("Phase 7: Final Report Generation")

    integrated_report_path = None
    if feedback_report_path and brief_content:
        console.print("[accent]Creating integrated full report...[/]")
        try:
            integrated_report_path = _generate_integrated_full_report(
                output_dir=output_dir_resolved,
                repo_name=repo_input,
                brief_content=brief_content,
                feedback_report_path=feedback_report_path,
            )
            console.print(f"[success]✓ Integrated full report generated[/]")
        except Exception as exc:
            console.print(f"[warning]Failed to generate integrated report: {exc}[/]")
    elif not feedback_report_path:
        console.print("[warning]Feedback report not available, skipping integrated report generation[/]")
    else:
        console.print("[warning]Brief report content not available, skipping integrated report generation[/]")

    return integrated_report_path


def _run_year_in_review_analysis(
    config: Config,
    output_dir: Path,
    year: Optional[int] = None,
) -> None:
    """Run year-in-review analysis across all active repositories.

    Args:
        config: Configuration object
        output_dir: Output directory for reports
        year: Specific year to analyze (default: current year)
    """
    from datetime import datetime
    from .year_in_review_reporter import YearInReviewReporter, RepositoryAnalysis

    if year is None:
        year = datetime.now().year

    console.print()
    console.print(f"[accent]🎊 Starting Year-in-Review Analysis for {year}[/]")
    console.rule(f"Year {year} in Review")

    # Initialize collector
    try:
        collector = Collector(config)
    except ValueError as exc:
        console.print_error(exc)
        raise typer.Exit(code=1) from exc

    # Get authenticated user
    author = cli_repository.get_authenticated_user(collector)

    # Discover repositories
    console.print()
    console.rule("Phase 1: Repository Discovery")
    with console.status(
        f"[accent]Finding repositories you contributed to in {year}...", spinner="dots"
    ):
        repositories = collector.get_year_in_review_repositories(year=year, min_contributions=3)

    if not repositories:
        console.print(f"[warning]No repositories found with contributions in {year}.[/]")
        console.print("[info]Suggestions:[/]")
        console.print("  • Try a different year with [accent]--year[/]")
        console.print("  • Check if your PAT has access to your repositories")
        raise typer.Exit(code=1)

    console.print(f"[success]✓ Found {len(repositories)} repositories with your contributions[/]")
    console.print()

    # Display repositories
    console.print("[info]Repositories to analyze:[/]")
    for idx, repo in enumerate(repositories, 1):
        full_name = repo.get("full_name", "")
        year_commits = repo.get("_year_commits", 0)
        console.print(f"  {idx}. {full_name} ({year_commits} commits)")
    console.print()

    # Analyze each repository in parallel
    console.print()
    console.rule("Phase 2: Repository Analysis")
    console.print(f"[accent]Analyzing {len(repositories)} repositories in parallel...[/]")

    output_dir_resolved = cli_helpers.resolve_output_dir(output_dir)

    # Create analysis tasks
    analysis_tasks = {}
    for repo_data in repositories:
        full_name = repo_data.get("full_name", "")
        if not full_name:
            continue

        key = f"repo_{full_name.replace('/', '__')}"
        analysis_tasks[key] = (
            _analyze_single_repository_for_year_review,
            (config, full_name, year, output_dir_resolved),
            f"Repository: {full_name}",
        )

    # Run analyses in parallel
    analysis_results = cli_helpers.run_parallel_tasks(
        analysis_tasks,
        max_workers=3,  # Limit concurrency to avoid rate limits
        timeout=600,  # 10 minutes per repository
        task_type=TaskType.ANALYSIS,
    )

    # Collect successful analyses
    repository_analyses = []
    for repo_data in repositories:
        full_name = repo_data.get("full_name", "")
        key = f"repo_{full_name.replace('/', '__')}"

        if key in analysis_results and analysis_results[key] is not None:
            repo_analysis = analysis_results[key]
            if repo_analysis:
                repository_analyses.append(repo_analysis)
        else:
            console.print(f"[warning]⚠ Skipped {full_name} due to analysis failure[/]")

    if not repository_analyses:
        console.print("[danger]All repository analyses failed.[/]")
        raise typer.Exit(code=1)

    console.print(f"[success]✓ Successfully analyzed {len(repository_analyses)} repositories[/]")

    # Generate year-in-review report
    console.print()
    console.rule("Phase 3: Generating Year-in-Review Report")

    year_reporter = YearInReviewReporter(output_dir=output_dir_resolved / "year-in-review")
    report_path = year_reporter.create_year_in_review_report(
        year=year,
        username=author,
        repository_analyses=repository_analyses,
    )

    # Display summary
    console.print()
    console.rule("Summary")
    console.print(f"[success]✓ Year-in-review analysis complete for {year}[/]")
    console.print(f"[success]✓ Analyzed {len(repository_analyses)} repositories[/]")
    console.print()
    console.print("[info]📊 Final Report:[/]")
    console.print(f"  • [accent]{report_path}[/]")
    console.print()
    console.print("[info]💡 Next steps:[/]")
    console.print(f"  • View the report: [accent]cat {report_path}[/]")
    console.print("  • Review individual repository reports in: [accent]reports/reviews/[/]")


def _analyze_single_repository_for_year_review(
    config: Config,
    repo_name: str,
    year: int,
    output_dir: Path,
) -> Optional[RepositoryAnalysis]:
    """Analyze a single repository for year-in-review.

    Args:
        config: Configuration object
        repo_name: Repository name (owner/repo)
        year: Year being analyzed
        output_dir: Output directory

    Returns:
        RepositoryAnalysis object or None if analysis fails
    """
    from .year_in_review_reporter import RepositoryAnalysis

    return cli_yearinreview.analyze_single_repository_for_year_review(
        config=config,
        repo_name=repo_name,
        year=year,
        output_dir=output_dir,
        run_feedback_analysis_func=_run_feedback_analysis,
        collect_detailed_feedback_func=cli_data_collection.collect_detailed_feedback,
    )


def _display_final_summary(
    author: str,
    repo_input: str,
    pr_results: list,
    integrated_report_path: Optional[Path],
    artifacts: List[tuple[str, Path]],
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


@app.command()
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
    from datetime import datetime, timedelta, timezone

    # Initialize configuration and components
    config = cli_helpers.load_config()

    # Handle year-in-review mode
    if year_in_review:
        _run_year_in_review_analysis(config, output_dir, year)
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
        repo_input = cli_repository.select_repository_interactive(collector)
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
    analyzer = Analyzer(web_base_url=config.server.web_url)
    output_dir_resolved = cli_helpers.resolve_output_dir(output_dir)

    # Create LLM client for reporter (used for generating summary quotes)
    from .llm import LLMClient
    llm_client = LLMClient(
        endpoint=config.llm.endpoint,
        model=config.llm.model,
        timeout=config.llm.timeout,
        web_url=config.server.web_url,
    )
    reporter = Reporter(output_dir=output_dir_resolved, llm_client=llm_client, web_url=config.server.web_url)

    # Execute analysis workflow
    author = cli_repository.get_authenticated_user(collector)
    collection = cli_data_collection.collect_personal_activity(collector, repo_input, months, filters, author)

    # Collect detailed feedback
    console.print()
    console.rule("Phase 2: Detailed Feedback Analysis")
    from github_feedback.constants import DAYS_PER_MONTH_APPROX
    since = datetime.now(timezone.utc) - timedelta(days=DAYS_PER_MONTH_APPROX * max(months, 1))
    detailed_feedback_snapshot = cli_data_collection.collect_detailed_feedback(
        collector, analyzer, config, repo_input, since, filters, author
    )

    # Collect year-end data
    console.print()
    console.rule("Phase 2.5: Year-End Review Data")
    monthly_trends_data, tech_stack_data, collaboration_data = cli_data_collection.collect_yearend_data(
        collector, repo_input, since, filters, author
    )

    # Compute metrics and display
    metrics = cli_metrics.compute_and_display_metrics(
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




@config_app.command("show")
def show_config() -> None:
    """Display current configuration settings.

    Shows your GitHub server URLs, LLM endpoint, and default settings.
    Sensitive values like tokens are masked for security.
    """
    from ._cli.commands.config_command import ConfigCommand

    command = ConfigCommand(console)
    command.show()


@config_app.command("set")
def config_set(
    key: str = typer.Argument(..., help="Configuration key in dot notation (e.g. llm.model)"),
    value: str = typer.Argument(..., help="Value to set"),
) -> None:
    """Set a configuration value.

    Examples:
        gfa config set llm.model gpt-4
        gfa config set llm.endpoint https://api.openai.com/v1/chat/completions
        gfa config set defaults.months 6
    """
    from ._cli.commands.config_command import ConfigCommand

    command = ConfigCommand(console)
    command.set(key, value)


@config_app.command("get")
def config_get(
    key: str = typer.Argument(..., help="Configuration key in dot notation (e.g. llm.model)"),
) -> None:
    """Get a configuration value.

    Examples:
        gfa config get llm.model
        gfa config get defaults.months
    """
    from ._cli.commands.config_command import ConfigCommand

    command = ConfigCommand(console)
    command.get(key)


@config_app.command("hosts")
def config_hosts(
    action: str = typer.Argument(
        ...,
        help="Action to perform: list, add, or remove"
    ),
    host: Optional[str] = typer.Argument(
        None,
        help="Host URL (required for add/remove actions)"
    ),
) -> None:
    """Manage custom enterprise hosts.

    Examples:
        gfa config hosts list
        gfa config hosts add https://github.company.com
        gfa config hosts remove https://github.company.com
    """
    from ._cli.commands.config_command import ConfigCommand

    command = ConfigCommand(console)
    command.hosts(action, host)


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
    from ._cli.commands.repository_command import RepositoryCommand

    command = RepositoryCommand(console)
    command.list_repos(sort=sort, limit=limit, org=org)


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
    """Suggest repositories for analysis based on activity and recency.

    This command recommends repositories that are actively maintained and
    likely to benefit from analysis. Suggestions are based on recent updates,
    stars, forks, and overall activity.

    Examples:
        gfa suggest-repos
        gfa suggest-repos --limit 5 --days 30
        gfa suggest-repos --sort stars
    """
    from ._cli.commands.repository_command import RepositoryCommand

    command = RepositoryCommand(console)
    command.suggest_repos(limit=limit, days=days, sort=sort)


@app.command(name="clear-cache")
def clear_cache() -> None:
    """Clear the API response cache.

    This can help resolve issues with stale or corrupted cached data
    that may cause JSON parsing errors or other unexpected behavior.

    Examples:
        gfa clear-cache
    """
    from ._cli.commands.cache_command import CacheCommand

    command = CacheCommand(console)
    command.clear_cache()


# Keep show-config as a deprecated alias for backward compatibility
@app.command(name="show-config", hidden=True, deprecated=True)
def show_config_deprecated() -> None:
    """Display current configuration settings (deprecated: use 'gfa config show')."""
    from ._cli.commands.config_command import ConfigCommand

    console.print("[warning]Note:[/] 'gfa show-config' is deprecated. Use 'gfa config show' instead.")
    console.print()
    command = ConfigCommand(console)
    command.show()
