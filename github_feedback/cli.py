"""Command line interface for the GitHub feedback toolkit."""

from __future__ import annotations

import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import typer

try:  # pragma: no cover - optional rich dependency
    from rich import box
    from rich.align import Align
    from rich.columns import Columns
    from rich.console import Group
    from rich.panel import Panel
    from rich.rule import Rule
    from rich.table import Table
    from rich.text import Text
except ModuleNotFoundError:  # pragma: no cover - fallback when rich is missing
    Align = None
    Columns = None
    Group = None
    Panel = None
    Rule = None
    Table = None
    Text = None
    box = None

from .analyzer import Analyzer
from .collector import Collector
from .config import Config
from .console import Console
from .llm import LLMClient
from .models import (
    AnalysisFilters,
    AnalysisStatus,
    DetailedFeedbackSnapshot,
    MetricSnapshot,
)
from .reporter import Reporter
from .review_reporter import ReviewReporter
from .reviewer import Reviewer
from .utils import validate_pat_format, validate_url, validate_repo_format, validate_months

app = typer.Typer(help="Analyze GitHub repositories and generate feedback reports.")
config_app = typer.Typer(help="Manage configuration settings")
app.add_typer(config_app, name="config")

console = Console()


def _resolve_output_dir(value: Path | str | object) -> Path:
    """Normalise CLI path inputs for both Typer and direct function calls."""

    if isinstance(value, Path):
        return value.expanduser()

    default_candidate = getattr(value, "default", value)
    if isinstance(default_candidate, Path):
        return default_candidate.expanduser()

    return Path(str(default_candidate)).expanduser()


def _load_config() -> Config:
    try:
        config = Config.load()
        config.validate_required_fields()
        return config
    except ValueError as exc:
        error_msg = str(exc)
        # Check if it's a multi-line error with bullet points
        if "\n" in error_msg:
            lines = error_msg.split("\n")
            console.print(f"[danger]{lines[0]}[/]")
            for line in lines[1:]:
                if line.strip():
                    console.print(f"  {line}")
        else:
            console.print(f"[danger]Configuration error:[/] {error_msg}")
        console.print()
        console.print("[info]Run [accent]gfa init[/] to set up your configuration")
        raise typer.Exit(code=1) from exc


def _select_repository_interactive(collector: Collector) -> Optional[str]:
    """Interactively select a repository from suggestions.

    Args:
        collector: Collector instance for fetching repositories

    Returns:
        Selected repository in owner/repo format, or None if cancelled
    """
    console.print("[info]Fetching repository suggestions...[/]")

    with console.status("[accent]Analyzing repositories...", spinner="bouncingBar"):
        try:
            suggestions = collector.suggest_repositories(limit=10, min_activity_days=90)
        except KeyboardInterrupt:
            raise
        except (requests.RequestException, ValueError) as exc:
            console.print(f"[danger]Error fetching suggestions:[/] {exc}")
            return None

    if not suggestions:
        console.print("[warning]No repository suggestions found.[/]")
        console.print("[info]Try manually specifying a repository with [accent]--repo[/]")
        return None

    # Display suggestions in a table
    if Table:
        console.print()
        table = Table(
            title="Suggested Repositories",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold cyan",
        )

        table.add_column("#", justify="right", style="dim", width=3)
        table.add_column("Repository", style="cyan", no_wrap=True)
        table.add_column("Description", style="dim")
        table.add_column("Activity", justify="right", style="success")

        for i, repo in enumerate(suggestions, 1):
            full_name = repo.get("full_name", "unknown/repo")
            description = repo.get("description") or "No description"
            if len(description) > 50:
                description = description[:47] + "..."

            stars = repo.get("stargazers_count", 0)
            forks = repo.get("forks_count", 0)
            activity = f"⭐{stars} 🍴{forks}"

            table.add_row(str(i), full_name, description, activity)

        console.print(table)
    else:
        # Fallback if rich is not available
        console.print("\nSuggested Repositories:\n")
        for i, repo in enumerate(suggestions, 1):
            full_name = repo.get("full_name", "unknown/repo")
            description = repo.get("description") or "No description"
            stars = repo.get("stargazers_count", 0)
            console.print(f"{i}. {full_name} - {description} (⭐ {stars})")
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

    # Determine if we're in interactive mode
    is_interactive = sys.stdin.isatty()

    # Prompt for missing required values only in interactive mode
    try:
        if pat is None:
            if is_interactive:
                pat = typer.prompt("GitHub Personal Access Token", hide_input=True)
            else:
                console.print("[danger]Error:[/] --pat is required in non-interactive mode")
                raise typer.Exit(code=1)

        if llm_endpoint is None:
            if is_interactive:
                llm_endpoint = typer.prompt("LLM API endpoint (OpenAI-compatible format)")
            else:
                console.print("[danger]Error:[/] --llm-endpoint is required in non-interactive mode")
                raise typer.Exit(code=1)

        if llm_model is None:
            if is_interactive:
                llm_model = typer.prompt("LLM model name (e.g. gpt-4, claude-3-5-sonnet-20241022)")
            else:
                console.print("[danger]Error:[/] --llm-model is required in non-interactive mode")
                raise typer.Exit(code=1)

        if enterprise_host is None and is_interactive:
            enterprise_host = typer.prompt(
                "GitHub Enterprise host (leave empty for github.com)",
                default="",
            )
    except (typer.Abort, KeyboardInterrupt, EOFError):
        console.print("\n[warning]Configuration cancelled by user.[/]")
        raise typer.Exit(code=0)

    # Validate inputs
    try:
        validate_pat_format(pat)
        validate_months(months)
        validate_url(llm_endpoint, "LLM endpoint")
    except ValueError as exc:
        console.print(f"[danger]Validation error:[/] {exc}")
        raise typer.Exit(code=1) from exc

    host_input = (enterprise_host or "").strip()
    if host_input:
        try:
            # Add scheme if missing
            if not host_input.startswith(("http://", "https://")):
                host_input = f"https://{host_input}"
            validate_url(host_input, "Enterprise host")
            host = host_input.rstrip("/")
        except ValueError as exc:
            console.print(f"[danger]Validation error:[/] {exc}")
            raise typer.Exit(code=1) from exc

        api_url = f"{host}/api/v3"
        graphql_url = f"{host}/api/graphql"
        web_url = host
    else:
        api_url = "https://api.github.com"
        graphql_url = "https://api.github.com/graphql"
        web_url = "https://github.com"

    config = Config.load()
    config.update_auth(pat)
    config.server.api_url = api_url
    config.server.graphql_url = graphql_url
    config.server.web_url = web_url
    config.llm.endpoint = llm_endpoint
    config.llm.model = llm_model
    config.defaults.months = months

    # Test LLM connection if requested
    if test_connection:
        console.print()
        with console.status("[accent]Testing LLM connection...", spinner="dots"):
            try:
                from .llm import LLMClient
                test_client = LLMClient(
                    endpoint=llm_endpoint,
                    model=llm_model,
                    timeout=10,
                )
                test_client.test_connection()
                console.print("[success]✓ LLM connection successful[/]")
            except KeyboardInterrupt:
                console.print("\n[warning]Configuration cancelled by user.[/]")
                raise typer.Exit(code=0)
            except (requests.RequestException, ValueError, ConnectionError) as exc:
                console.print(f"[warning]⚠ LLM connection test failed: {exc}[/]")
                try:
                    if is_interactive and not typer.confirm("Save configuration anyway?", default=True):
                        console.print("[info]Configuration not saved[/]")
                        raise typer.Exit(code=1)
                except (typer.Abort, KeyboardInterrupt, EOFError):
                    console.print("\n[warning]Configuration cancelled by user.[/]")
                    raise typer.Exit(code=0)

    config.dump()
    console.print("[success]✓ Configuration saved successfully[/]")
    console.print("[success]✓ GitHub token stored securely in system keyring[/]")
    console.print()
    show_config()


def _render_metrics(metrics: MetricSnapshot) -> None:
    """Render metrics with a visually rich presentation."""

    if (
        Table is None
        or Panel is None
        or Columns is None
        or Text is None
        or Group is None
        or Align is None
    ):
        console.print(f"Analysis complete for {metrics.repo}")
        console.print(f"Timeframe: {metrics.months} months")
        console.print(f"Status: {metrics.status.value}")
        for key, value in metrics.summary.items():
            console.print(f"- {key.title()}: {value}")
        if metrics.highlights:
            console.print("Highlights:")
            for highlight in metrics.highlights:
                console.print(f"  • {highlight}")
        return

    status_styles = {
        AnalysisStatus.CREATED: "warning",
        AnalysisStatus.COLLECTED: "accent",
        AnalysisStatus.ANALYSED: "success",
        AnalysisStatus.REPORTED: "accent",
    }
    status_style = status_styles.get(metrics.status, "accent")

    header = Panel(
        Group(
            Align.center(Text("인사이트 준비 완료", style="title")),
            Align.center(Text(metrics.repo, style="repo")),
            Align.center(Text(f"{metrics.months}개월 회고", style="muted")),
        ),
        border_style="accent",
        padding=(1, 4),
    )

    console.print(header)
    console.print(
        Rule(
            title=f"[{status_style}]상태 • {metrics.status.value.upper()}[/]",
            style="divider",
            characters="━",
            align="center",
        )
    )

    if metrics.summary:
        summary_grid = Table.grid(padding=(0, 2))
        summary_grid.add_column(justify="right", style="label")
        summary_grid.add_column(style="value")
        for key, value in metrics.summary.items():
            summary_grid.add_row(key.title(), str(value))

        summary_panel = Panel(summary_grid, border_style="frame", title="핵심 지표", title_align="left")
    else:
        summary_panel = Panel(Text("사용 가능한 요약 지표가 없습니다", style="muted"), border_style="frame")

    stat_panels = []
    for domain, domain_stats in metrics.stats.items():
        stat_table = Table(
            box=box.MINIMAL,
            show_edge=False,
            pad_edge=False,
            expand=True,
        )
        stat_table.add_column("지표", style="label")
        stat_table.add_column("값", style="value")
        for stat_name, stat_value in domain_stats.items():
            if isinstance(stat_value, (int, float)):
                formatted = f"{stat_value:.2f}" if not isinstance(stat_value, int) else f"{stat_value:,}"
            else:
                formatted = str(stat_value)
            stat_table.add_row(stat_name.replace("_", " ").title(), formatted)

        stat_panel = Panel(
            stat_table,
            title=domain.replace("_", " ").title(),
            border_style="accent",
            padding=(0, 1),
        )
        stat_panels.append(stat_panel)

    sections = [summary_panel]
    if stat_panels:
        sections.append(Columns(stat_panels, equal=True, expand=True))

    console.print(*sections)

    if metrics.highlights:
        highlights_text = Text("\n".join(f"• {item}" for item in metrics.highlights), style="value")
        highlights_panel = Panel(highlights_text, title="주요 하이라이트", border_style="frame")
        console.print(highlights_panel)

    if metrics.spotlight_examples:
        spotlight_panels = []
        for category, entries in metrics.spotlight_examples.items():
            spotlight_text = Text("\n".join(f"• {entry}" for entry in entries), style="value")
            spotlight_panels.append(
                Panel(
                    spotlight_text,
                    title=category.replace("_", " ").title(),
                    border_style="accent",
                    padding=(1, 2),
                )
            )
        console.print(Columns(spotlight_panels, expand=True))

    if metrics.awards:
        awards_text = Text("\n".join(f"🏆 {award}" for award in metrics.awards), style="value")
        console.print(Panel(awards_text, title="수상 내역", border_style="accent"))

    if metrics.evidence:
        evidence_panels = []
        for domain, links in metrics.evidence.items():
            evidence_text = Text("\n".join(f"🔗 {link}" for link in links), style="value")
            evidence_panels.append(
                Panel(
                    evidence_text,
                    title=domain.replace("_", " ").title(),
                    border_style="frame",
                    padding=(1, 2),
                )
            )
        console.print(Columns(evidence_panels, expand=True))


def _collect_detailed_feedback(
    collector: Collector,
    analyzer: Analyzer,
    config: Config,
    repo: str,
    since: datetime,
    filters: AnalysisFilters,
    author: Optional[str] = None,
) -> Optional[DetailedFeedbackSnapshot]:
    """Collect and analyze detailed feedback data."""
    from concurrent.futures import ThreadPoolExecutor, as_completed
    from .llm import LLMClient

    console.print("[accent]Collecting detailed feedback data...", style="accent")

    try:
        # Collect detailed data in parallel
        data_collection_tasks = {
            "commits": (collector.collect_commit_messages, (repo, since, filters), {"limit": 100, "author": author}, "commit messages"),
            "pr_titles": (collector.collect_pr_titles, (repo, since, filters), {"limit": 100, "author": author}, "PR titles"),
            "review_comments": (collector.collect_review_comments_detailed, (repo, since, filters), {"limit": 100, "author": author}, "review comments"),
            "issues": (collector.collect_issue_details, (repo, since, filters), {"limit": 100, "author": author}, "issues"),
        }

        collected_data = {}
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {
                executor.submit(func, *args, **kwargs): (key, label)
                for key, (func, args, kwargs, label) in data_collection_tasks.items()
            }

            completed = 0
            total = len(futures)
            for future in as_completed(futures, timeout=120):
                key, label = futures[future]
                try:
                    collected_data[key] = future.result(timeout=120)
                    completed += 1
                    console.print(f"[success]✓ {label} collected ({completed}/{total})", style="success")
                except KeyboardInterrupt:
                    raise
                except TimeoutError:
                    console.print(f"[warning]✗ {label} collection timed out after 120s", style="warning")
                    collected_data[key] = []
                except Exception as e:
                    console.print(f"[warning]✗ {label} collection failed: {e}", style="warning")
                    collected_data[key] = []

        commits_data = collected_data.get("commits", [])
        pr_titles_data = collected_data.get("pr_titles", [])
        review_comments_data = collected_data.get("review_comments", [])
        issues_data = collected_data.get("issues", [])

        # Analyze using LLM
        llm_client = LLMClient(
            endpoint=config.llm.endpoint,
            model=config.llm.model,
            timeout=config.llm.timeout,
            max_files_in_prompt=config.llm.max_files_in_prompt,
            max_files_with_patch_snippets=config.llm.max_files_with_patch_snippets,
        )

        # Parallelize LLM analysis calls
        console.print("[accent]Analyzing feedback in parallel...", style="accent")

        analysis_tasks = {
            "commit_messages": (llm_client.analyze_commit_messages, commits_data, "commits"),
            "pr_titles": (llm_client.analyze_pr_titles, pr_titles_data, "PR titles"),
            "review_tone": (llm_client.analyze_review_tone, review_comments_data, "review tone"),
            "issue_quality": (llm_client.analyze_issue_quality, issues_data, "issues"),
        }

        results = {}
        with ThreadPoolExecutor(max_workers=4) as executor:
            # Submit all tasks
            futures = {
                executor.submit(func, data): (key, label)
                for key, (func, data, label) in analysis_tasks.items()
            }

            # Collect results with progress indication
            completed = 0
            total = len(futures)
            for future in as_completed(futures, timeout=180):
                key, label = futures[future]
                try:
                    results[key] = future.result(timeout=180)
                    completed += 1
                    console.print(f"[success]✓ {label} analyzed ({completed}/{total})", style="success")
                except KeyboardInterrupt:
                    raise
                except TimeoutError:
                    console.print(f"[warning]✗ {label} analysis timed out after 180s", style="warning")
                    results[key] = None
                except Exception as e:
                    console.print(f"[warning]✗ {label} analysis failed: {e}", style="warning")
                    results[key] = None

        commit_analysis = results.get("commit_messages")
        pr_title_analysis = results.get("pr_titles")
        review_tone_analysis = results.get("review_tone")
        issue_analysis = results.get("issue_quality")

        # Build detailed feedback snapshot
        detailed_feedback_snapshot = analyzer.build_detailed_feedback(
            commit_analysis=commit_analysis,
            pr_title_analysis=pr_title_analysis,
            review_tone_analysis=review_tone_analysis,
            issue_analysis=issue_analysis,
        )

        console.print("[success]✓ Detailed feedback analysis complete", style="success")
        return detailed_feedback_snapshot

    except Exception as exc:
        console.print(
            f"[warning]Warning: Detailed feedback analysis failed: {exc}", style="warning"
        )
        console.print("[cyan]Continuing with standard analysis...", style="cyan")
        return None


def _prepare_metrics_payload(metrics: MetricSnapshot) -> dict:
    """Prepare metrics data for serialization."""
    metrics_payload = {
        "repo": metrics.repo,
        "months": metrics.months,
        "generated_at": metrics.generated_at.isoformat(),
        "status": metrics.status.value,
        "summary": metrics.summary,
        "stats": metrics.stats,
        "evidence": metrics.evidence,
        "highlights": metrics.highlights,
        "spotlight_examples": metrics.spotlight_examples,
        "yearbook_story": metrics.yearbook_story,
        "awards": metrics.awards,
    }

    # Add date range if available
    if metrics.since_date:
        metrics_payload["since_date"] = metrics.since_date.isoformat()
    if metrics.until_date:
        metrics_payload["until_date"] = metrics.until_date.isoformat()

    # Add detailed feedback
    if metrics.detailed_feedback:
        metrics_payload["detailed_feedback"] = metrics.detailed_feedback.to_dict()

    # Add monthly trends
    if metrics.monthly_trends:
        metrics_payload["monthly_trends"] = [trend.to_dict() for trend in metrics.monthly_trends]

    # Add monthly insights
    if metrics.monthly_insights:
        metrics_payload["monthly_insights"] = metrics.monthly_insights.to_dict()

    # Add tech stack analysis
    if metrics.tech_stack:
        metrics_payload["tech_stack"] = metrics.tech_stack.to_dict()

    # Add collaboration network
    if metrics.collaboration:
        metrics_payload["collaboration"] = metrics.collaboration.to_dict()

    # Add reflection prompts
    if metrics.reflection_prompts:
        metrics_payload["reflection_prompts"] = metrics.reflection_prompts.to_dict()

    # Add year-end review
    if metrics.year_end_review:
        metrics_payload["year_end_review"] = metrics.year_end_review.to_dict()

    return metrics_payload


def _generate_artifacts(
    metrics: MetricSnapshot,
    reporter: Reporter,
    output_dir: Path,
    metrics_payload: dict,
) -> List[tuple[str, Path]]:
    """Generate all report artifacts."""
    artifacts = []

    # Save metrics
    metrics_path = persist_metrics(output_dir=output_dir, metrics_data=metrics_payload)
    artifacts.append(("Metrics snapshot", metrics_path))

    # Generate markdown report
    markdown_path = reporter.generate_markdown(metrics)
    artifacts.append(("Markdown report", markdown_path))

    # Generate HTML report with charts
    html_path = reporter.generate_html(metrics)
    artifacts.append(("HTML report", html_path))

    # Generate prompt packets
    prompt_artifacts = reporter.generate_prompt_packets(metrics)
    for prompt_request, prompt_path in prompt_artifacts:
        artifacts.append((f"Prompt • {prompt_request.title}", prompt_path))

    return artifacts


def _check_repository_activity(
    collection: CollectionResult, repo_input: str, months: int
) -> None:
    """Check if repository has any activity and exit if not.

    Args:
        collection: Collection result to check
        repo_input: Repository name
        months: Number of months analyzed

    Raises:
        typer.Exit: If no activity is found
    """
    if (collection.commits == 0 and collection.pull_requests == 0 and
        collection.reviews == 0 and collection.issues == 0):
        console.print("[warning]No activity found in the repository for the specified period.[/]")
        console.print(f"[info]Repository:[/] {repo_input}")
        console.print(f"[info]Period:[/] Last {months} months")
        console.print("[info]Suggestions:[/]")
        console.print("  • Try increasing the analysis period: [accent]gfa init --months 24[/]")
        console.print("  • Verify the repository has commits, PRs, or issues")
        console.print("  • Check if your PAT has access to this repository")
        raise typer.Exit(code=1)


def _collect_yearend_data(
    collector: Collector,
    repo_input: str,
    since: datetime,
    filters: AnalysisFilters,
    author: Optional[str] = None,
) -> tuple[Optional[Any], Optional[Any], Optional[Any]]:
    """Collect year-end review data in parallel.

    Args:
        collector: Data collector instance
        repo_input: Repository name
        since: Start date for data collection
        filters: Analysis filters
        author: Optional GitHub username to filter by author

    Returns:
        Tuple of (monthly_trends_data, tech_stack_data, collaboration_data)
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed

    console.print("[accent]Collecting year-end review data in parallel...", style="accent")

    # Get PR metadata once for reuse
    _, pr_metadata = collector.list_pull_requests(repo_input, since, filters, author)

    yearend_tasks = {
        "monthly_trends": (
            collector.collect_monthly_trends,
            (repo_input, since, filters),
            "monthly trends"
        ),
        "tech_stack": (
            collector.collect_tech_stack,
            (repo_input, pr_metadata),
            "tech stack"
        ),
        "collaboration": (
            collector.collect_collaboration_network,
            (repo_input, pr_metadata, filters),
            "collaboration network"
        ),
    }

    yearend_data = {}
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {
            executor.submit(func, *args): (key, label)
            for key, (func, args, label) in yearend_tasks.items()
        }

        completed = 0
        total = len(futures)
        for future in as_completed(futures, timeout=180):
            key, label = futures[future]
            try:
                yearend_data[key] = future.result(timeout=180)
                completed += 1
                console.print(f"[success]✓ {label} collected ({completed}/{total})", style="success")
            except KeyboardInterrupt:
                raise
            except TimeoutError:
                console.print(f"[warning]✗ {label} collection timed out after 180s", style="warning")
                yearend_data[key] = None
            except Exception as exc:
                console.print(f"[warning]✗ {label} collection failed: {exc}", style="warning")
                yearend_data[key] = None

    return (
        yearend_data.get("monthly_trends"),
        yearend_data.get("tech_stack"),
        yearend_data.get("collaboration"),
    )


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
        console.print(f"[danger]Error:[/] {exc}")
        return None, []

    llm_client = LLMClient(
        endpoint=config.llm.endpoint,
        model=config.llm.model,
        timeout=config.llm.timeout,
        max_files_in_prompt=config.llm.max_files_in_prompt,
        max_files_with_patch_snippets=config.llm.max_files_with_patch_snippets,
    )

    reviewer = Reviewer(collector=collector, llm=llm_client)

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
    results = []

    # Generate PR reviews
    for idx, pr_number in enumerate(pr_numbers, 1):
        with console.status(
            f"[accent]Analyzing PR #{pr_number} ({idx}/{total_prs})...", spinner="line"
        ):
            artefact_path, summary_path, markdown_path = reviewer.review_pull_request(
                repo=repo_input,
                number=pr_number,
            )
        results.append((pr_number, artefact_path, summary_path, markdown_path))
        console.print(f"[success]✓ PR #{pr_number} reviewed ({idx}/{total_prs})", style="success")

    # Generate integrated report
    output_dir_resolved = _resolve_output_dir(output_dir)
    review_reporter = ReviewReporter(
        output_dir=output_dir_resolved,
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
    brief_report_path: Path,
    feedback_report_path: Path,
) -> Path:
    """Generate an integrated report combining brief and feedback reports.

    Args:
        output_dir: Output directory for the integrated report
        repo_name: Repository name in owner/repo format
        brief_report_path: Path to the brief report markdown file
        feedback_report_path: Path to the feedback integrated report markdown file

    Returns:
        Path to the generated integrated report
    """
    # Read brief report
    try:
        with open(brief_report_path, "r", encoding="utf-8") as f:
            brief_content = f.read()
    except FileNotFoundError:
        console.print(f"[warning]Brief report not found at {brief_report_path}[/]")
        brief_content = "_Brief report not available._"

    # Read feedback report
    try:
        with open(feedback_report_path, "r", encoding="utf-8") as f:
            feedback_content = f.read()
    except FileNotFoundError:
        console.print(f"[warning]Feedback report not found at {feedback_report_path}[/]")
        feedback_content = "_Feedback report not available._"

    # Generate integrated report
    integrated_content = f"""# {repo_name} 전체 분석 및 PR 리뷰 보고서

이 보고서는 레포지토리 전체 분석(brief)과 PR 리뷰 분석(feedback)을 통합한 종합 보고서입니다.

## 목차

1. [레포지토리 개요 (Repository Brief)](#1-레포지토리-개요-repository-brief)
2. [PR 리뷰 분석 (PR Feedback)](#2-pr-리뷰-분석-pr-feedback)
3. [종합 요약](#3-종합-요약)

---

## 1. 레포지토리 개요 (Repository Brief)

{brief_content}

---

## 2. PR 리뷰 분석 (PR Feedback)

{feedback_content}

---

## 3. 종합 요약

이 보고서는 **{repo_name}** 레포지토리에 대한 전체 분석과 PR 리뷰를 통합하여 제공합니다.

### 주요 내용

- **레포지토리 분석**: 커밋, PR, 리뷰, 이슈 등 전체 활동 지표와 인사이트
- **PR 리뷰 분석**: 인증된 사용자의 PR들에 대한 AI 기반 상세 리뷰

### 활용 방법

1. **레포지토리 개요**: 프로젝트의 전체적인 건강도와 트렌드를 파악하세요
2. **PR 리뷰**: 개별 PR의 강점과 개선 사항을 확인하여 코드 품질을 향상시키세요
3. **지속적 개선**: 정기적으로 분석을 실행하여 팀의 성장을 추적하세요

---

*Generated by GitHub Feedback Analysis Tool*
*Report generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*
"""

    # Save integrated report
    output_dir.mkdir(parents=True, exist_ok=True)
    integrated_report_path = output_dir / "integrated_full_report.md"

    with open(integrated_report_path, "w", encoding="utf-8") as f:
        f.write(integrated_content)

    return integrated_report_path


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
) -> None:
    """Analyze repository activity and generate detailed reports with PR feedback.

    This command collects commits, PRs, reviews, and issues from a GitHub
    repository, analyzes all PRs authored by you, then generates comprehensive
    reports with insights and recommendations.

    Examples:
        gfa feedback --repo torvalds/linux
        gfa feedback --repo myorg/myrepo --output custom_reports/
        gfa feedback --interactive
    """
    from datetime import datetime, timedelta, timezone

    config = _load_config()
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
        console.print(f"[danger]Error:[/] {exc}")
        console.print("[info]Hint:[/] Check your GitHub token with [accent]gfa show-config[/]")
        raise typer.Exit(code=1) from exc

    # Handle interactive mode or no repo specified
    if interactive or repo is None:
        repo_input = _select_repository_interactive(collector)
        if not repo_input:
            console.print("[warning]No repository selected.[/]")
            raise typer.Exit(code=0)
    else:
        repo_input = repo.strip()

    analyzer = Analyzer(web_base_url=config.server.web_url)
    output_dir_resolved = _resolve_output_dir(output_dir)
    reporter = Reporter(output_dir=output_dir_resolved)

    try:
        validate_repo_format(repo_input)
    except ValueError as exc:
        console.print(f"[danger]Validation error:[/] {exc}")
        console.print("[info]Example:[/] [accent]gfa feedback --repo torvalds/linux[/]")
        raise typer.Exit(code=1) from exc

    # Phase 0: Get authenticated user
    console.print()
    console.rule("Phase 0: Authentication")
    with console.status("[accent]Retrieving authenticated user...", spinner="dots"):
        try:
            author = collector.get_authenticated_user()
            console.print(f"[success]✓ Authenticated as: {author}[/]")
        except (ValueError, PermissionError) as exc:
            console.print(f"[error]Failed to get authenticated user: {exc}[/]")
            raise typer.Exit(code=1) from exc

    # Phase 1: Collect personal activity data
    console.print()
    console.rule("Phase 1: Personal Activity Collection")
    console.print(f"[accent]Collecting personal activity for {author}...[/]")
    with console.status("[accent]Collecting repository data...", spinner="bouncingBar"):
        collection = collector.collect(repo=repo_input, months=months, filters=filters, author=author)

    # Check if repository has any activity
    _check_repository_activity(collection, repo_input, months)

    # Phase 2: Collect detailed feedback
    console.print()
    console.rule("Phase 2: Detailed Feedback Analysis")
    since = datetime.now(timezone.utc) - timedelta(days=30 * max(months, 1))
    detailed_feedback_snapshot = _collect_detailed_feedback(
        collector, analyzer, config, repo_input, since, filters, author
    )

    # Phase 2.5: Collect year-end review data in parallel
    console.print()
    console.rule("Phase 2.5: Year-End Review Data")
    monthly_trends_data, tech_stack_data, collaboration_data = _collect_yearend_data(
        collector, repo_input, since, filters, author
    )

    # Phase 3: Compute metrics
    console.print()
    console.rule("Phase 3: Metrics Computation")
    with console.status("[accent]Synthesizing insights...", spinner="dots"):
        metrics = analyzer.compute_metrics(
            collection,
            detailed_feedback=detailed_feedback_snapshot,
            monthly_trends_data=monthly_trends_data,
            tech_stack_data=tech_stack_data,
            collaboration_data=collaboration_data,
        )
    console.print("[success]✓ Metrics computed successfully[/]")

    # Phase 4: Generate reports
    console.print()
    console.rule("Phase 4: Report Generation")
    metrics_payload = _prepare_metrics_payload(metrics)
    artifacts = _generate_artifacts(metrics, reporter, output_dir, metrics_payload)

    # Phase 5: Display results
    console.print()
    console.rule("Analysis Summary")
    _render_metrics(metrics)
    console.rule("Artifacts")
    for label, path in artifacts:
        console.print(f"[success]{label} generated:[/]", f"[value]{path}[/]")
    console.print()
    console.print("[success]✓ Personal activity analysis complete![/]")

    # Final summary
    console.print()
    console.rule("Summary")
    console.print(f"[success]✓ Analyzed personal activity for {author}[/]")
    console.print()
    console.print("[info]Next steps:[/]")
    console.print("  • View the report: [accent]cat reports/report.md[/]")
    console.print("  • View the HTML report: [accent]open reports/report.html[/]")


def persist_metrics(output_dir: Path, metrics_data: dict, filename: str = "metrics.json") -> Path:
    """Persist raw metrics to disk for later reporting."""

    output_dir = output_dir.expanduser()
    output_dir.mkdir(parents=True, exist_ok=True)
    metrics_path = output_dir / filename
    import json

    with metrics_path.open("w", encoding="utf-8") as handle:
        json.dump(metrics_data, handle, indent=2)

    return metrics_path


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

    config = _load_config()
    data = config.to_display_dict()

    if Table is None:
        console.print("GitHub Feedback Configuration")
        for section, values in data.items():
            console.print(f"[{section}]")
            for key, value in values.items():
                console.print(f"{key} = {value}")
            console.print("")
        return

    table = Table(
        title="GitHub Feedback Configuration",
        box=box.ROUNDED,
        title_style="title",
        border_style="frame",
        expand=True,
        show_lines=True,
    )
    table.add_column("Section", style="label", no_wrap=True)
    table.add_column("Values", style="value")

    for section, values in data.items():
        rendered_values = "\n".join(f"[label]{k}[/]: [value]{v}[/]" for k, v in values.items())
        table.add_row(f"[accent]{section}[/]", rendered_values)

    console.print(table)


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
    try:
        config = Config.load()
        config.set_value(key, value)
        config.dump()
        console.print(f"[success]✓ Configuration updated:[/] {key} = {value}")
    except ValueError as exc:
        console.print(f"[danger]Error:[/] {exc}")
        raise typer.Exit(code=1) from exc


@config_app.command("get")
def config_get(
    key: str = typer.Argument(..., help="Configuration key in dot notation (e.g. llm.model)"),
) -> None:
    """Get a configuration value.

    Examples:
        gfa config get llm.model
        gfa config get defaults.months
    """
    try:
        config = Config.load()
        value = config.get_value(key)
        console.print(f"{key} = {value}")
    except ValueError as exc:
        console.print(f"[danger]Error:[/] {exc}")
        raise typer.Exit(code=1) from exc


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
    config = _load_config()

    try:
        collector = Collector(config)
    except ValueError as exc:
        console.print(f"[danger]Error:[/] {exc}")
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

    # Create a rich table
    if Table:
        table = Table(
            title=f"{'Organization' if org else 'Your'} Repositories",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold cyan",
        )

        table.add_column("Repository", style="cyan", no_wrap=True)
        table.add_column("Description", style="dim")
        table.add_column("Stars", justify="right", style="warning")
        table.add_column("Forks", justify="right", style="success")
        table.add_column("Updated", justify="right", style="dim")

        for repo in repos:
            full_name = repo.get("full_name", "unknown/repo")
            description = repo.get("description") or "No description"
            if len(description) > 50:
                description = description[:47] + "..."

            stars = str(repo.get("stargazers_count", 0))
            forks = str(repo.get("forks_count", 0))

            # Format updated date
            updated_at = repo.get("updated_at", "")
            updated_str = ""
            if updated_at:
                try:
                    from datetime import datetime

                    updated_dt = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
                    updated_dt = updated_dt.replace(tzinfo=None)
                    days_ago = (datetime.now() - updated_dt).days

                    if days_ago == 0:
                        updated_str = "today"
                    elif days_ago == 1:
                        updated_str = "yesterday"
                    elif days_ago < 30:
                        updated_str = f"{days_ago}d ago"
                    elif days_ago < 365:
                        updated_str = f"{days_ago // 30}mo ago"
                    else:
                        updated_str = f"{days_ago // 365}y ago"
                except (ValueError, AttributeError):
                    updated_str = "unknown"

            table.add_row(full_name, description, stars, forks, updated_str)

        console.print(table)
    else:
        # Fallback if rich is not available
        for i, repo in enumerate(repos, 1):
            full_name = repo.get("full_name", "unknown/repo")
            description = repo.get("description") or "No description"
            stars = repo.get("stargazers_count", 0)
            console.print(f"{i}. {full_name} - {description} (⭐ {stars})")


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
    config = _load_config()

    try:
        collector = Collector(config)
    except ValueError as exc:
        console.print(f"[danger]Error:[/] {exc}")
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

    # Create a rich table
    if Table:
        table = Table(
            title="Suggested Repositories for Analysis",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold cyan",
        )

        table.add_column("Rank", justify="right", style="dim", width=4)
        table.add_column("Repository", style="cyan", no_wrap=True)
        table.add_column("Description", style="dim")
        table.add_column("Activity", justify="right", style="success")
        table.add_column("Updated", justify="right", style="warning")

        for i, repo in enumerate(suggestions, 1):
            full_name = repo.get("full_name", "unknown/repo")
            description = repo.get("description") or "No description"
            if len(description) > 45:
                description = description[:42] + "..."

            # Activity indicator
            stars = repo.get("stargazers_count", 0)
            forks = repo.get("forks_count", 0)
            issues = repo.get("open_issues_count", 0)
            activity = f"⭐{stars} 🍴{forks} 📋{issues}"

            # Format updated date
            updated_at = repo.get("updated_at", "")
            updated_str = ""
            if updated_at:
                try:
                    from datetime import datetime

                    updated_dt = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
                    updated_dt = updated_dt.replace(tzinfo=None)
                    days_ago = (datetime.now() - updated_dt).days

                    if days_ago == 0:
                        updated_str = "today"
                    elif days_ago == 1:
                        updated_str = "yesterday"
                    elif days_ago < 30:
                        updated_str = f"{days_ago}d ago"
                    else:
                        updated_str = f"{days_ago // 30}mo ago"
                except (ValueError, AttributeError):
                    updated_str = "unknown"

            rank_str = f"#{i}"
            table.add_row(rank_str, full_name, description, activity, updated_str)

        console.print(table)
        console.print()
        console.print(
            "[info]To analyze a repository, use:[/] [accent]gfa feedback --repo <owner/name>[/]"
        )
    else:
        # Fallback if rich is not available
        console.print("Suggested Repositories for Analysis:\n")
        for i, repo in enumerate(suggestions, 1):
            full_name = repo.get("full_name", "unknown/repo")
            description = repo.get("description") or "No description"
            stars = repo.get("stargazers_count", 0)
            console.print(f"{i}. {full_name} - {description} (⭐ {stars})")


# Keep show-config as a deprecated alias for backward compatibility
@app.command(name="show-config", hidden=True, deprecated=True)
def show_config_deprecated() -> None:
    """Display current configuration settings (deprecated: use 'gfa config show')."""
    console.print("[warning]Note:[/] 'gfa show-config' is deprecated. Use 'gfa config show' instead.")
    console.print()
    show_config()
