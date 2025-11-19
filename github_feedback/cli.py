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

app = typer.Typer(help="Analyze GitHub repositories and generate feedback reports.")
config_app = typer.Typer(help="Manage configuration settings")
app.add_typer(config_app, name="config")

console = Console()
logger = logging.getLogger(__name__)


@contextmanager
def handle_user_interruption(message: str = "Operation cancelled by user."):
    """Context manager to handle user interruptions consistently.

    Args:
        message: Custom message to display when operation is cancelled

    Yields:
        None

    Raises:
        typer.Exit: Always exits with code 0 when interrupted
    """
    try:
        yield
    except (typer.Abort, KeyboardInterrupt, EOFError):
        console.print(f"\n[warning]{message}[/]")
        raise typer.Exit(code=0)


def _validate_collected_data(data: Optional[List], data_type: str) -> List:
    """Validate and log collection results.

    Args:
        data: Collected data list or None
        data_type: Type of data being validated (for logging)

    Returns:
        Empty list if data is None or empty, otherwise the original data
    """
    if data is None:
        logger.warning(
            "Data collection failed",
            extra={
                "component": "feedback_collector",
                "data_type": data_type,
                "status": "failed",
                "count": 0
            }
        )
        return []
    elif not data:
        logger.info(
            "No data found for analysis",
            extra={
                "component": "feedback_collector",
                "data_type": data_type,
                "status": "empty",
                "count": 0
            }
        )
        return []
    else:
        logger.info(
            "Data collection completed",
            extra={
                "component": "feedback_collector",
                "data_type": data_type,
                "status": "success",
                "count": len(data)
            }
        )
        return data


def _handle_task_exception(
    exception: Exception,
    key: str,
    label: str,
    timeout: int,
    task_type: TaskType,
) -> tuple[Exception, Any, str]:
    """Handle exceptions from parallel tasks with consistent error creation.

    Args:
        exception: The exception that occurred
        key: Task identifier
        label: Human-readable task label
        timeout: Timeout value in seconds
        task_type: Type of task (TaskType.COLLECTION or TaskType.ANALYSIS)

    Returns:
        Tuple of (error, default_result, status_indicator)
    """
    # Re-raise keyboard interrupts and system exits
    if isinstance(exception, (KeyboardInterrupt, SystemExit)):
        raise exception

    is_timeout = isinstance(exception, TimeoutError)
    is_analysis = task_type == TaskType.ANALYSIS

    if is_timeout:
        error = (
            LLMTimeoutError(f"{label} timed out after {timeout}s", analysis_type=key)
            if is_analysis
            else CollectionTimeoutError(f"{label} timed out after {timeout}s", source=key)
        )
        status_indicator = "⚠"
    else:
        error = (
            LLMAnalysisError(f"{label} failed: {exception}", analysis_type=key)
            if is_analysis
            else CollectionError(f"{label} failed: {exception}", source=key)
        )
        status_indicator = "✗"

    default_result = None if is_analysis else []
    return error, default_result, status_indicator


def _run_parallel_tasks(
    tasks: Dict[str, Tuple[Callable, Tuple, str]],
    max_workers: int,
    timeout: int,
    task_type: TaskType = TaskType.COLLECTION,
) -> Dict[str, Any]:
    """Run multiple tasks in parallel with progress indicator and consistent error handling.

    Args:
        tasks: Dict mapping task keys to (func, args, label) tuples where:
            - func: Callable to execute
            - args: Tuple of arguments to pass to func
            - label: Human-readable task label for progress display
        max_workers: Maximum number of concurrent workers
        timeout: Timeout in seconds for each task
        task_type: Type of task (TaskType.COLLECTION or TaskType.ANALYSIS)

    Returns:
        Dict mapping task keys to results (None for failed tasks)
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed

    results = {}
    total = len(tasks)
    timeout_occurred = False

    # Use Rich Progress bar if available
    if Progress is not None:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeRemainingColumn(),
            console=console.rich_console if hasattr(console, 'rich_console') else None
        ) as progress:
            task_id = progress.add_task(
                f"[cyan]{task_type.capitalize()}...",
                total=total
            )

            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {
                    executor.submit(func, *args): (key, label)
                    for key, (func, args, label) in tasks.items()
                }

                for future in as_completed(futures, timeout=timeout):
                    key, label = futures[future]
                    try:
                        results[key] = future.result(timeout=timeout)
                        progress.update(task_id, advance=1, description=f"[green]✓ {label}")
                    except Exception as e:
                        error, default_result, status_indicator = _handle_task_exception(
                            e, key, label, timeout, task_type
                        )
                        console.print(f"[warning]{status_indicator} {error}", style="warning")
                        results[key] = default_result
                        color = "yellow" if status_indicator == "⚠" else "red"
                        progress.update(task_id, advance=1, description=f"[{color}]{status_indicator} {label}")

                        # Track if timeout occurred
                        if status_indicator == "⚠":
                            timeout_occurred = True
    else:
        # Fallback to simple progress without Rich
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(func, *args): (key, label)
                for key, (func, args, label) in tasks.items()
            }

            completed = 0
            for future in as_completed(futures, timeout=timeout):
                key, label = futures[future]
                try:
                    results[key] = future.result(timeout=timeout)
                    completed += 1
                    console.print(f"[success]✓ {label} completed ({completed}/{total})", style="success")
                except Exception as e:
                    error, default_result, status_indicator = _handle_task_exception(
                        e, key, label, timeout, task_type
                    )
                    console.print(f"[warning]{status_indicator} {error}", style="warning")
                    results[key] = default_result

                    # Track if timeout occurred
                    if status_indicator == "⚠":
                        timeout_occurred = True

    # Display guidance if timeout occurred
    if timeout_occurred:
        console.print()
        console.print("[cyan]💡 Timeout이 발생했나요?[/]")
        console.print("[dim]   걱정하지 마세요! 같은 명령어를 다시 실행하면 이미 수집된 데이터를 활용하여[/]")
        console.print("[dim]   작업을 이어서 진행합니다. 캐시 덕분에 60-70% 더 빠르게 완료됩니다.[/]")
        console.print()

    return results


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


def _load_default_hosts() -> list[str]:
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


def _select_enterprise_host_interactive(custom_hosts: list[str]) -> Optional[Tuple[str, bool]]:
    """Interactive enterprise host selection with preset and custom options.

    Args:
        custom_hosts: List of user-configured custom enterprise hosts

    Returns:
        Tuple of (selected_host, should_save) or None if cancelled
        - selected_host: The enterprise host URL (empty string for github.com)
        - should_save: Whether to save this host to custom list
    """
    # Load default example hosts from config
    default_hosts = _load_default_hosts()

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
    with handle_user_interruption("Configuration cancelled by user."):
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

        # Enterprise host selection with interactive menu
        should_save_host = False
        if enterprise_host is None and is_interactive:
            # Load config to get custom hosts
            temp_config = Config.load()
            result = _select_enterprise_host_interactive(temp_config.server.custom_enterprise_hosts)
            if result is None:
                # User cancelled
                console.print("\n[warning]Configuration cancelled by user.[/]")
                raise typer.Exit(code=0)
            enterprise_host, should_save_host = result

    # Validate inputs
    try:
        validate_pat_format(pat)
        validate_months(months)
        validate_url(llm_endpoint, "LLM endpoint")
    except ValueError as exc:
        console.print_validation_error(str(exc))
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
            console.print_validation_error(str(exc))
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

    # Save custom enterprise host if requested
    if should_save_host and host_input and host_input not in config.server.custom_enterprise_hosts:
        config.server.custom_enterprise_hosts.append(host_input)
        console.print(f"[success]✓ Saved '{host_input}' to your custom host list[/]")

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
                with handle_user_interruption("Configuration cancelled by user."):
                    if is_interactive and not typer.confirm("Save configuration anyway?", default=True):
                        console.print("[info]Configuration not saved[/]")
                        raise typer.Exit(code=1)

    config.dump()
    console.print("[success]✓ Configuration saved successfully[/]")
    console.print("[success]✓ GitHub token stored securely in system keyring[/]")
    console.print()
    _print_config_summary()


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
    """Collect and analyze detailed feedback data in parallel.

    This function collects four types of feedback data and analyzes them using LLM:
    1. Commit messages - for quality analysis
    2. PR titles - for clarity analysis
    3. Review comments - for tone analysis
    4. Issue details - for quality analysis

    Args:
        collector: Data collector instance
        analyzer: Metrics analyzer instance
        config: Configuration with LLM settings
        repo: Repository name in owner/repo format
        since: Start date for data collection
        filters: Analysis filters to apply
        author: Optional GitHub username to filter by author

    Returns:
        DetailedFeedbackSnapshot with LLM analysis results,
        or None if collection/analysis fails

    Raises:
        KeyboardInterrupt: User interrupted the operation
    """
    from .llm import LLMClient
    import time

    start_time = time.time()
    console.print("[accent]Collecting detailed feedback data...", style="accent")

    logger.info(
        "Starting detailed feedback collection",
        extra={
            "component": "feedback_collector",
            "repo": repo,
            "since": since.isoformat(),
            "author": author or "all"
        }
    )

    try:
        # Prepare data collection tasks
        collection_tasks = {
            "commits": (
                lambda: collector.collect_commit_messages(
                    repo, since, filters, COLLECTION_LIMITS['commit_messages'], author
                ),
                (),
                "commit messages"
            ),
            "pr_titles": (
                lambda: collector.collect_pr_titles(
                    repo, since, filters, COLLECTION_LIMITS['pr_titles'], author
                ),
                (),
                "PR titles"
            ),
            "review_comments": (
                lambda: collector.collect_review_comments_detailed(
                    repo, since, filters, COLLECTION_LIMITS['review_comments'], author
                ),
                (),
                "review comments"
            ),
            "issues": (
                lambda: collector.collect_issue_details(
                    repo, since, filters, COLLECTION_LIMITS['issues'], author
                ),
                (),
                "issues"
            ),
        }

        # Collect data in parallel
        collected_data = _run_parallel_tasks(
            collection_tasks,
            PARALLEL_CONFIG['max_workers_data_collection'],
            PARALLEL_CONFIG['collection_timeout'],
            task_type=TaskType.COLLECTION
        )

        # Validate and extract collected data
        commits_data = _validate_collected_data(collected_data.get("commits"), "commits")
        pr_titles_data = _validate_collected_data(collected_data.get("pr_titles"), "PR titles")
        review_comments_data = _validate_collected_data(collected_data.get("review_comments"), "review comments")
        issues_data = _validate_collected_data(collected_data.get("issues"), "issues")

        # Analyze using LLM
        llm_client = LLMClient(
            endpoint=config.llm.endpoint,
            model=config.llm.model,
            timeout=config.llm.timeout,
            max_files_in_prompt=config.llm.max_files_in_prompt,
            max_files_with_patch_snippets=config.llm.max_files_with_patch_snippets,
            web_url=config.server.web_url,
        )

        # Parallelize LLM analysis calls
        console.print("[accent]Analyzing feedback in parallel...", style="accent")

        analysis_tasks = {
            "commit_messages": (lambda: llm_client.analyze_commit_messages(commits_data, repo), (), "commits"),
            "pr_titles": (lambda: llm_client.analyze_pr_titles(pr_titles_data), (), "PR titles"),
            "review_tone": (lambda: llm_client.analyze_review_tone(review_comments_data), (), "review tone"),
            "issue_quality": (lambda: llm_client.analyze_issue_quality(issues_data, config.server.web_url, repo), (), "issues"),
            "personal_development": (lambda: llm_client.analyze_personal_development(pr_titles_data, review_comments_data, repo), (), "personal development"),
        }

        results = _run_parallel_tasks(
            analysis_tasks,
            PARALLEL_CONFIG['max_workers_llm_analysis'],
            PARALLEL_CONFIG['analysis_timeout'],
            task_type=TaskType.ANALYSIS
        )

        commit_analysis = results.get("commit_messages")
        pr_title_analysis = results.get("pr_titles")
        review_tone_analysis = results.get("review_tone")
        issue_analysis = results.get("issue_quality")
        personal_development_analysis = results.get("personal_development")

        # Build detailed feedback snapshot
        detailed_feedback_snapshot = analyzer.build_detailed_feedback(
            commit_analysis=commit_analysis,
            pr_title_analysis=pr_title_analysis,
            review_tone_analysis=review_tone_analysis,
            issue_analysis=issue_analysis,
            personal_development_analysis=personal_development_analysis,
        )

        elapsed_time = time.time() - start_time
        logger.info(
            "Detailed feedback analysis completed successfully",
            extra={
                "component": "feedback_collector",
                "repo": repo,
                "duration_seconds": round(elapsed_time, 2),
                "status": "success"
            }
        )
        console.print("[success]✓ Detailed feedback analysis complete", style="success")
        return detailed_feedback_snapshot

    except (requests.RequestException, json.JSONDecodeError, ValueError, KeyError) as exc:
        elapsed_time = time.time() - start_time
        logger.warning(
            "Detailed feedback analysis failed",
            extra={
                "component": "feedback_collector",
                "repo": repo,
                "duration_seconds": round(elapsed_time, 2),
                "error_type": type(exc).__name__,
                "error_message": str(exc),
                "status": "failed"
            },
            exc_info=True
        )
        console.print(
            f"[warning]Warning: Detailed feedback analysis failed: {exc}", style="warning"
        )

        # Provide actionable guidance based on exception type
        if isinstance(exc, requests.RequestException):
            console.print(
                "[cyan]💡 해결 방법: 네트워크 연결을 확인하거나 LLM endpoint 설정을 검토하세요.",
                style="cyan"
            )
            console.print(
                "[dim]  설정 확인: gfa config show",
                style="dim"
            )
        elif isinstance(exc, json.JSONDecodeError):
            console.print(
                "[cyan]💡 해결 방법: LLM 응답 형식이 올바르지 않습니다. 모델 설정을 확인하세요.",
                style="cyan"
            )
            console.print(
                "[dim]  다른 모델을 시도하거나 config.llm.model을 확인하세요.",
                style="dim"
            )
        elif isinstance(exc, (ValueError, KeyError)):
            console.print(
                "[cyan]💡 해결 방법: 수집된 데이터 형식에 문제가 있습니다.",
                style="cyan"
            )
            console.print(
                "[dim]  --debug 플래그로 상세 로그를 확인하거나 이슈를 제출해주세요.",
                style="dim"
            )

        console.print("[cyan]Continuing with standard analysis...", style="cyan")
        return None
    except KeyboardInterrupt:
        console.print("\n[warning]Analysis interrupted by user", style="warning")
        raise


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

    # Add year-end review
    if metrics.year_end_review:
        metrics_payload["year_end_review"] = metrics.year_end_review.to_dict()

    return metrics_payload


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
    metrics_path = persist_metrics(output_dir=output_dir, metrics_data=metrics_payload)
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
    if not collection.has_activity():
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

    # Use common parallel task runner
    yearend_data = _run_parallel_tasks(
        tasks=yearend_tasks,
        max_workers=PARALLEL_CONFIG['max_workers_yearend'],
        timeout=PARALLEL_CONFIG['yearend_timeout'],
        task_type="collection"
    )

    # Convert empty lists to None for consistency with downstream code
    return (
        yearend_data.get("monthly_trends") or None,
        yearend_data.get("tech_stack") or None,
        yearend_data.get("collaboration") or None,
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

    review_results = _run_parallel_tasks(
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
    output_dir_resolved = _resolve_output_dir(output_dir)
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


def _generate_final_summary_table(personal_dev_path: Path) -> str:
    """Generate final summary table with strengths, improvements, and growth.

    Args:
        personal_dev_path: Path to personal_development.json file

    Returns:
        Markdown formatted final summary section with tables
    """
    import json

    # Try to load personal development data
    try:
        with open(personal_dev_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        # If file doesn't exist or can't be read, return empty summary
        return "## 📋 종합 피드백\n\n개인 성장 분석 데이터를 찾을 수 없습니다."

    # Extract top 3 strengths, top 2 improvements, top 3 growth indicators
    strengths = data.get("strengths", [])[:3]
    improvements = data.get("improvement_areas", [])[:2]
    growth = data.get("growth_indicators", [])[:3]

    # Build summary section
    lines = ["## 📋 종합 피드백", ""]

    # Strengths table
    if strengths:
        lines.append("### ✨ 주요 장점")
        lines.append("")
        lines.append("| 장점 | 근거 |")
        lines.append("|------|------|")
        for strength in strengths:
            category = strength.get("category", "기타")
            description = strength.get("description", "")
            evidence = strength.get("evidence", [])
            evidence_text = "<br>".join([f"• {e}" for e in evidence]) if evidence else "근거 없음"
            lines.append(f"| **{category}**: {description} | {evidence_text} |")
        lines.append("")

    # Improvements table
    if improvements:
        lines.append("### 💡 보완점")
        lines.append("")
        lines.append("| 보완점 | 근거 |")
        lines.append("|--------|------|")
        for improvement in improvements:
            category = improvement.get("category", "기타")
            description = improvement.get("description", "")
            evidence = improvement.get("evidence", [])
            evidence_text = "<br>".join([f"• {e}" for e in evidence]) if evidence else "근거 없음"
            lines.append(f"| **{category}**: {description} | {evidence_text} |")
        lines.append("")

    # Growth indicators table
    if growth:
        lines.append("### 🌱 올해 성장한 점")
        lines.append("")
        lines.append("| 성장 영역 | 근거 |")
        lines.append("|-----------|------|")
        for indicator in growth:
            aspect = indicator.get("aspect", "기타")
            description = indicator.get("description", "")
            progress_summary = indicator.get("progress_summary", "")
            before = indicator.get("before_examples", [])
            after = indicator.get("after_examples", [])

            evidence_parts = []
            if progress_summary:
                evidence_parts.append(f"**진전 사항:** {progress_summary}")
            if before:
                evidence_parts.append(f"**초기:** {', '.join(before[:2])}")
            if after:
                evidence_parts.append(f"**현재:** {', '.join(after[:2])}")

            evidence_text = "<br>".join(evidence_parts) if evidence_parts else "근거 없음"
            lines.append(f"| **{aspect}**: {description} | {evidence_text} |")
        lines.append("")

    return "\n".join(lines)


def _extract_section_content(content: str, section_header: str, next_section_prefix: str = "##") -> str:
    """Extract content of a specific section from markdown.

    Args:
        content: Full markdown content
        section_header: Header to look for (e.g., "## 🏆 Awards Cabinet")
        next_section_prefix: Prefix for next section (default "##")

    Returns:
        Extracted section content or empty string if not found
    """
    import re

    # Escape special regex characters in header
    escaped_header = re.escape(section_header)

    # Find section start
    pattern = rf'^{escaped_header}\s*$'
    match = re.search(pattern, content, re.MULTILINE)
    if not match:
        return ""

    start_pos = match.end()

    # Find next section of same or higher level
    next_section_pattern = rf'^{re.escape(next_section_prefix)} '
    next_match = re.search(next_section_pattern, content[start_pos:], re.MULTILINE)

    if next_match:
        end_pos = start_pos + next_match.start()
        return content[start_pos:end_pos].strip()

    return content[start_pos:].strip()


def _create_executive_summary(brief_content: str, feedback_content: str, output_dir: Path) -> str:
    """Create executive summary from brief and feedback reports.

    Args:
        brief_content: Brief report content
        feedback_content: Feedback report content
        output_dir: Output directory to find personal_development.json

    Returns:
        Executive summary markdown section
    """
    lines = ["## 🎯 한눈에 보기 (Executive Summary)", ""]
    lines.append("> 핵심 성과와 개선 포인트를 빠르게 파악하세요")
    lines.append("")

    # Extract key achievements from brief (awards section)
    awards_section = _extract_section_content(brief_content, "## 🏆 Awards Cabinet")
    if awards_section:
        # Count total awards
        import re
        award_matches = re.findall(r'\|\s*[^|]+\s*\|\s*([^|]+)\s*\|', awards_section)
        total_awards = len([m for m in award_matches if m.strip() and m.strip() not in ['어워드', '-----']])
        if total_awards > 0:
            lines.append(f"**🏆 획득 어워드**: {total_awards}개")

    # Extract highlights from brief
    highlights_section = _extract_section_content(brief_content, "## ✨ Growth Highlights")
    if highlights_section:
        import re
        highlight_matches = re.findall(r'\|\s*\d+\s*\|\s*([^|]+)\s*\|', highlights_section)
        if highlight_matches and len(highlight_matches) > 0:
            lines.append("")
            lines.append("**✨ 주요 성과 Top 3:**")
            for i, highlight in enumerate(highlight_matches[:3], 1):
                lines.append(f"{i}. {highlight.strip()}")

    # Extract improvement areas from personal development
    personal_dev_path = output_dir / "reviews" / "_temp_personal_dev.json"
    # Try to find personal_development.json in reviews subdirectories
    reviews_dir = output_dir / "reviews"
    if reviews_dir.exists():
        for repo_dir in reviews_dir.iterdir():
            if repo_dir.is_dir():
                pd_path = repo_dir / "personal_development.json"
                if pd_path.exists():
                    personal_dev_path = pd_path
                    break

    if personal_dev_path.exists():
        try:
            import json
            with open(personal_dev_path, "r", encoding="utf-8") as f:
                pd_data = json.load(f)

            improvements = pd_data.get("improvement_areas", [])[:2]
            if improvements:
                lines.append("")
                lines.append("**💡 주요 개선점 Top 2:**")
                for i, imp in enumerate(improvements, 1):
                    category = imp.get("category", "")
                    desc = imp.get("description", "")
                    lines.append(f"{i}. **{category}**: {desc}")

            # Extract next focus areas
            next_focus = pd_data.get("next_focus_areas", [])[:3]
            if next_focus:
                lines.append("")
                lines.append("**🎯 다음 집중 영역:**")
                for i, focus in enumerate(next_focus, 1):
                    lines.append(f"{i}. {focus}")
        except (json.JSONDecodeError, OSError):
            pass

    lines.append("")
    lines.append("---")
    lines.append("")
    return "\n".join(lines)


def _create_improved_toc() -> str:
    """Create improved table of contents with better structure."""
    lines = ["## 📑 목차", ""]

    sections = [
        ("1", "🎯 한눈에 보기", "핵심 성과와 개선점 요약"),
        ("2", "🏆 주요 성과", "어워드와 성장 하이라이트"),
        ("3", "💡 개선 피드백", "장점, 보완점, 실행 계획"),
        ("4", "📊 상세 분석", "월별 트렌드, 기술 스택, 협업, 회고"),
        ("5", "📝 부록", "개별 PR 리뷰 및 상세 사례"),
    ]

    for num, title, desc in sections:
        lines.append(f"{num}. **{title}** - {desc}")

    lines.append("")
    lines.append("---")
    lines.append("")
    return "\n".join(lines)


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
    # Read feedback report with comprehensive error handling
    try:
        with open(feedback_report_path, "r", encoding="utf-8") as f:
            feedback_content = f.read()
    except FileNotFoundError:
        console.print(f"[warning]Feedback report not found at {feedback_report_path}[/]")
        feedback_content = "_Feedback report not available._"
    except PermissionError as exc:
        console.print(f"[warning]Permission denied reading {feedback_report_path}[/]")
        raise RuntimeError(f"Permission denied reading feedback report: {exc}") from exc
    except OSError as exc:
        console.print(f"[warning]Error reading feedback report: {exc}[/]")
        raise RuntimeError(f"Failed to read feedback report: {exc}") from exc

    # Extract key sections from brief
    awards_section = _extract_section_content(brief_content, "## 🏆 Awards Cabinet")
    highlights_section = _extract_section_content(brief_content, "## ✨ Growth Highlights")
    monthly_trends_section = _extract_section_content(brief_content, "## 📈 Monthly Trends")
    feedback_section = _extract_section_content(brief_content, "## 💡 Detailed Feedback")
    retrospective_section = _extract_section_content(brief_content, "## 🔍 Deep Retrospective Analysis")
    tech_stack_section = _extract_section_content(brief_content, "## 💻 Tech Stack Analysis")
    collaboration_section = _extract_section_content(brief_content, "## 🤝 PR 활동 요약")
    witch_section = _extract_section_content(brief_content, "## 🔮 마녀의 독설")

    # Extract key sections from feedback
    personal_dev_section = _extract_section_content(feedback_content, "## 👤 개인 성장 분석")
    strengths_section = _extract_section_content(feedback_content, "## ✨ 장점")
    improvements_section = _extract_section_content(feedback_content, "## 💡 보완점")
    growth_section = _extract_section_content(feedback_content, "## 🌱 올해 성장한 점")

    # Create executive summary
    exec_summary = _create_executive_summary(brief_content, feedback_content, output_dir)

    # Create improved TOC
    toc = _create_improved_toc()

    # Generate integrated report with improved structure
    integrated_content = f"""# 📊 {repo_name} 통합 분석 보고서

> 레포지토리 전체 분석과 PR 리뷰를 통합한 종합 보고서입니다.

{exec_summary}

{toc}

## 2. 🏆 주요 성과

> 이번 기간 동안 달성한 어워드와 성장 하이라이트

### 🏅 획득 어워드

{awards_section if awards_section else "_어워드 정보가 없습니다._"}

### ✨ 성장 하이라이트

{highlights_section if highlights_section else "_하이라이트 정보가 없습니다._"}

---

## 3. 💡 개선 피드백

> 구체적인 장점, 보완점, 실행 가능한 제안

{personal_dev_section if personal_dev_section else "_개인 성장 분석 정보가 없습니다._"}

### 🔮 마녀의 독설

{witch_section if witch_section else "_마녀의 독설 인사이트가 없습니다._"}

### 코드 품질 피드백

{feedback_section if feedback_section else "_상세 피드백 정보가 없습니다._"}

---

## 4. 📊 상세 분석

> 데이터 기반의 심층 분석 (필요한 섹션을 클릭하여 펼쳐보세요)

<details>
<summary><b>📈 월별 활동 트렌드</b> (클릭하여 펼치기)</summary>

{monthly_trends_section if monthly_trends_section else "_월별 트렌드 정보가 없습니다._"}

</details>

<details>
<summary><b>💻 기술 스택 분석</b> (클릭하여 펼치기)</summary>

{tech_stack_section if tech_stack_section else "_기술 스택 정보가 없습니다._"}

</details>

<details>
<summary><b>🤝 협업 분석</b> (클릭하여 펼치기)</summary>

{collaboration_section if collaboration_section else "_협업 정보가 없습니다._"}

</details>

<details>
<summary><b>🔍 심층 회고</b> (클릭하여 펼치기)</summary>

{retrospective_section if retrospective_section else "_회고 분석 정보가 없습니다._"}

</details>

---

## 5. 📝 부록

> 개별 PR 리뷰 및 상세 사례 (필요시 펼쳐보세요)

<details>
<summary><b>📝 상세 사례</b> (클릭하여 펼치기)</summary>

{growth_section if growth_section else ""}

{strengths_section if strengths_section else ""}

{improvements_section if improvements_section else ""}

</details>

---

<div align="center">

*Generated by GitHub Feedback Analysis Tool*
*Report generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*

</div>
"""

    # Save integrated report with comprehensive error handling
    from .utils import FileSystemManager

    try:
        FileSystemManager.ensure_directory(output_dir)
    except PermissionError as exc:
        raise RuntimeError(
            f"Permission denied creating directory {output_dir}: {exc}"
        ) from exc
    except OSError as exc:
        raise RuntimeError(
            f"Failed to create directory {output_dir}: {exc}"
        ) from exc

    integrated_report_path = output_dir / "integrated_full_report.md"

    # Validate path before writing
    if integrated_report_path.exists() and not integrated_report_path.is_file():
        raise RuntimeError(
            f"Cannot write to {integrated_report_path}: path exists but is not a file"
        )

    try:
        with open(integrated_report_path, "w", encoding="utf-8") as f:
            f.write(integrated_content)
    except PermissionError as exc:
        raise RuntimeError(
            f"Permission denied writing to {integrated_report_path}: {exc}"
        ) from exc
    except OSError as exc:
        # Check for specific errors
        if exc.errno == 28:  # ENOSPC - No space left on device
            raise RuntimeError(
                f"No space left on device while writing to {integrated_report_path}"
            ) from exc
        raise RuntimeError(
            f"Failed to write integrated report to {integrated_report_path}: {exc}"
        ) from exc

    return integrated_report_path


def _get_authenticated_user(collector: Collector) -> str:
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


def _collect_personal_activity(
    collector: Collector,
    repo_input: str,
    months: int,
    filters: AnalysisFilters,
    author: str,
):
    """Collect personal activity data for a repository.

    Args:
        collector: Collector instance
        repo_input: Repository name
        months: Number of months to collect
        filters: Analysis filters
        author: GitHub username

    Returns:
        Collection result

    Raises:
        typer.Exit: If no activity found
    """
    console.print()
    console.rule("Phase 1: Personal Activity Collection")
    console.print(f"[accent]Collecting personal activity for {author}...[/]")
    with console.status("[accent]Collecting repository data...", spinner="bouncingBar"):
        collection = collector.collect(repo=repo_input, months=months, filters=filters, author=author)

    _check_repository_activity(collection, repo_input, months)
    return collection


def _compute_and_display_metrics(
    analyzer: Analyzer,
    collection,
    detailed_feedback_snapshot: Optional[DetailedFeedbackSnapshot],
    monthly_trends_data,
    tech_stack_data,
    collaboration_data,
) -> MetricSnapshot:
    """Compute metrics and display summary.

    Args:
        analyzer: Analyzer instance
        collection: Collection result
        detailed_feedback_snapshot: Detailed feedback data
        monthly_trends_data: Monthly trends data
        tech_stack_data: Tech stack data
        collaboration_data: Collaboration data

    Returns:
        Computed metrics snapshot
    """
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

    console.print()
    console.rule("Analysis Summary")
    _render_metrics(metrics)

    return metrics


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
    metrics_payload = _prepare_metrics_payload(metrics)
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
    author = _get_authenticated_user(collector)

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

    output_dir_resolved = _resolve_output_dir(output_dir)

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
    analysis_results = _run_parallel_tasks(
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


def _get_year_in_review_metrics_dir(output_dir: Path) -> Path:
    """Return the directory that stores per-repository metrics for Year-in-Review."""

    return output_dir / "year-in-review" / "metrics"


def _get_year_in_review_metrics_path(output_dir: Path, repo_name: str) -> Path:
    """Return the canonical metrics path for the given repository."""

    safe_repo = repo_name.replace("/", "__")
    return _get_year_in_review_metrics_dir(output_dir) / f"{safe_repo}.json"


def _get_legacy_year_in_review_metrics_path(output_dir: Path, repo_name: str) -> Path:
    """Return the legacy metrics path that stored metrics inside repo-named folders."""

    safe_repo = repo_name.replace("/", "__")
    return output_dir / safe_repo / "metrics.json"


def _load_year_in_review_metrics_data(
    primary_path: Path, legacy_path: Path
) -> tuple[dict, bool]:
    """Load metrics data from the new or legacy path.

    Returns:
        Tuple containing the loaded metrics (or empty dict) and a flag indicating whether
        the data originated from the legacy path.
    """

    import json

    for path, is_legacy in ((primary_path, False), (legacy_path, True)):
        if path.exists():
            try:
                with path.open("r", encoding="utf-8") as handle:
                    return json.load(handle), is_legacy
            except Exception:
                return {}, is_legacy

    return {}, False


def _cleanup_legacy_metrics_path(legacy_path: Path) -> None:
    """Remove the legacy metrics file/directory if it exists and is now unused."""

    try:
        if legacy_path.exists():
            legacy_path.unlink()
        parent = legacy_path.parent
        if parent.exists():
            parent.rmdir()
    except OSError:
        # If the directory isn't empty or can't be removed, ignore silently.
        pass


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
    import json
    from datetime import datetime, timedelta
    from .year_in_review_reporter import RepositoryAnalysis

    try:
        # Get authenticated user
        collector = Collector(config)
        author = collector.get_authenticated_user()
        safe_repo = repo_name.replace("/", "__")

        # Calculate year date range
        since = datetime(year, 1, 1)
        until = datetime(year, 12, 31, 23, 59, 59)

        # Get PR count for the year
        filters = AnalysisFilters(
            include_branches=[],
            exclude_branches=[],
            include_paths=[],
            exclude_paths=[],
            include_languages=[],
            exclude_bots=True,
        )

        # Collect PRs authored in the year
        pr_numbers = collector.list_authored_pull_requests(
            repo=repo_name,
            author=author,
            state="all",
        )

        # Run feedback analysis (generates integrated_report.md and personal_development.json)
        feedback_report_path, pr_results = _run_feedback_analysis(
            config=config,
            repo_input=repo_name,
            output_dir=output_dir,
        )

        # Collect detailed feedback for communication skills analysis
        console.print(f"[dim]📊 Collecting detailed feedback for {repo_name}...[/]")
        analyzer = Analyzer(web_base_url=config.server.web_url)
        detailed_feedback_snapshot = _collect_detailed_feedback(
            collector=collector,
            analyzer=analyzer,
            config=config,
            repo=repo_name,
            since=since,
            filters=filters,
            author=author,
        )

        # Save detailed feedback to metrics.json for later retrieval
        if detailed_feedback_snapshot:
            console.print(f"[dim]💾 Saving detailed feedback to metrics.json...[/]")
            metrics_path = _get_year_in_review_metrics_path(output_dir, repo_name)
            legacy_metrics_path = _get_legacy_year_in_review_metrics_path(output_dir, repo_name)
            from .utils import FileSystemManager

            metrics_dir = metrics_path.parent
            FileSystemManager.ensure_directory(metrics_dir)

            metrics_data, loaded_from_legacy = _load_year_in_review_metrics_data(
                metrics_path, legacy_metrics_path
            )

            # Add detailed_feedback to metrics
            metrics_data["detailed_feedback"] = detailed_feedback_snapshot.to_dict()

            # Save updated metrics
            import json

            with metrics_path.open("w", encoding="utf-8") as f:
                json.dump(metrics_data, f, indent=2, ensure_ascii=False)

            if loaded_from_legacy:
                _cleanup_legacy_metrics_path(legacy_metrics_path)

            console.print(f"[success]✅ Saved detailed feedback to {metrics_path}[/]")

        # Load personal development data
        reviews_dir = output_dir / "reviews" / safe_repo
        personal_dev_path = reviews_dir / "personal_development.json"

        strengths = []
        improvements = []
        growth_indicators = []
        tech_stack = {}

        # Communication skills data
        commit_message_quality = None
        pr_title_quality = None
        review_tone_quality = None
        issue_quality = None
        commit_stats = {}
        pr_title_stats = {}
        review_tone_stats = {}
        issue_stats = {}

        if personal_dev_path.exists():
            with open(personal_dev_path, "r", encoding="utf-8") as f:
                personal_dev = json.load(f)

            strengths = personal_dev.get("strengths", [])
            improvements = personal_dev.get("improvement_areas", [])
            growth_indicators = personal_dev.get("growth_indicators", [])

        # Load metrics.json for detailed feedback (commit message quality, review tone, etc.)
        metrics_path = _get_year_in_review_metrics_path(output_dir, repo_name)
        legacy_metrics_path = _get_legacy_year_in_review_metrics_path(output_dir, repo_name)
        metrics_data, _ = _load_year_in_review_metrics_data(metrics_path, legacy_metrics_path)
        if metrics_data:
            try:
                # Extract detailed feedback
                detailed_feedback = metrics_data.get("detailed_feedback", {})

                # Commit message quality
                if "commit_feedback" in detailed_feedback:
                    cf = detailed_feedback["commit_feedback"]
                    total_commits = cf.get("total_commits", 0)
                    good_messages = cf.get("good_messages", 0)
                    poor_messages = cf.get("poor_messages", 0)

                    if total_commits > 0:
                        commit_message_quality = (good_messages / total_commits) * 100
                        commit_stats = {
                            "total": total_commits,
                            "good": good_messages,
                            "poor": poor_messages
                        }

                # PR title quality
                if "pr_title_feedback" in detailed_feedback:
                    pf = detailed_feedback["pr_title_feedback"]
                    total_prs = pf.get("total_prs", 0)
                    clear_titles = pf.get("clear_titles", 0)
                    unclear_titles = pf.get("unclear_titles", 0)

                    if total_prs > 0:
                        pr_title_quality = (clear_titles / total_prs) * 100
                        pr_title_stats = {
                            "total": total_prs,
                            "clear": clear_titles,
                            "unclear": unclear_titles
                        }

                # Review tone quality
                if "review_tone_feedback" in detailed_feedback:
                    rtf = detailed_feedback["review_tone_feedback"]
                    constructive = rtf.get("constructive_reviews", 0)
                    harsh = rtf.get("harsh_reviews", 0)
                    neutral = rtf.get("neutral_reviews", 0)
                    total_reviews = constructive + harsh + neutral

                    if total_reviews > 0:
                        review_tone_quality = (constructive / total_reviews) * 100
                        review_tone_stats = {
                            "constructive": constructive,
                            "harsh": harsh,
                            "neutral": neutral
                        }

                # Issue quality
                if "issue_feedback" in detailed_feedback:
                    isf = detailed_feedback["issue_feedback"]
                    total_issues = isf.get("total_issues", 0)
                    clear_issues = isf.get("clear_issues", 0)
                    unclear_issues = isf.get("unclear_issues", 0)

                    if total_issues > 0:
                        issue_quality = (clear_issues / total_issues) * 100
                        issue_stats = {
                            "total": total_issues,
                            "clear": clear_issues,
                            "unclear": unclear_issues
                        }

                console.print(f"[success]✅ Loaded communication skills data from metrics.json[/]")
            except Exception as e:
                console.print(f"[warning]⚠️  Could not load metrics.json: {e}[/]")

        # Collect tech stack data
        try:
            # Get PR metadata for tech stack analysis
            # Use a much broader time window to get sufficient data for tech stack analysis
            # Instead of only PRs created in the target year, analyze recent repository activity
            from datetime import timedelta
            tech_stack_since = datetime(year - 2, 1, 1)  # Look back 2 years for better tech stack data

            console.print(f"[dim]🔍 Fetching PRs for tech stack analysis (since {tech_stack_since.year}-01-01)...[/]")
            _, pr_metadata = collector.list_pull_requests(
                repo=repo_name,
                since=tech_stack_since,  # Use broader window for tech stack analysis
                filters=filters,
                author=None  # Analyze all PRs in repo, not just user's
            )

            console.print(f"[dim]📊 Analyzing tech stack from {len(pr_metadata)} PRs (since {tech_stack_since.year})[/]")

            if not pr_metadata:
                console.print(f"[warning]⚠️  No PRs found for tech stack analysis in {repo_name}[/]")
            else:
                tech_stack_snapshot = collector.collect_tech_stack(
                    repo=repo_name,
                    pr_metadata=pr_metadata
                )

                if tech_stack_snapshot:
                    tech_stack = {lang: count for lang, count in tech_stack_snapshot.items()}
                    console.print(f"[success]✅ Found {len(tech_stack)} technologies in tech stack[/]")
                    # Debug: Print top 5 technologies
                    if tech_stack:
                        sorted_tech = sorted(tech_stack.items(), key=lambda x: x[1], reverse=True)[:5]
                        tech_preview = ", ".join([f"{lang}({count})" for lang, count in sorted_tech])
                        console.print(f"[dim]   Top technologies: {tech_preview}[/]")
                else:
                    console.print(f"[warning]⚠️  Tech stack analysis returned empty for {repo_name}[/]")
        except Exception as exc:
            import traceback
            console.print(f"[error]❌ Could not collect tech stack for {repo_name}:[/]")
            console.print(f"[error]   Error: {exc}[/]")
            console.print(f"[dim]{traceback.format_exc()}[/]")

        # Get total commit count
        owner, repo = repo_name.split("/", 1)
        all_commits = collector.api_client.get_user_commits_in_repo(
            owner, repo, author, max_pages=10
        )
        total_commits = len(all_commits)

        # Get commits in the year
        year_commits_params = {
            "author": author,
            "since": since.isoformat() + "Z",
            "until": until.isoformat() + "Z",
        }
        year_commits = collector.api_client.request_all(
            f"/repos/{owner}/{repo}/commits",
            params=year_commits_params,
        )

        return RepositoryAnalysis(
            full_name=repo_name,
            pr_count=len(pr_results),
            commit_count=total_commits,
            year_commits=len(year_commits),
            integrated_report_path=feedback_report_path,
            personal_dev_path=personal_dev_path if personal_dev_path.exists() else None,
            strengths=strengths,
            improvements=improvements,
            growth_indicators=growth_indicators,
            tech_stack=tech_stack,
            commit_message_quality=commit_message_quality,
            pr_title_quality=pr_title_quality,
            review_tone_quality=review_tone_quality,
            issue_quality=issue_quality,
            commit_stats=commit_stats,
            pr_title_stats=pr_title_stats,
            review_tone_stats=review_tone_stats,
            issue_stats=issue_stats,
        )

    except Exception as exc:
        console.print(f"[warning]Failed to analyze {repo_name}: {exc}[/]")
        return None


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
    config = _load_config()

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
    analyzer = Analyzer(web_base_url=config.server.web_url)
    output_dir_resolved = _resolve_output_dir(output_dir)

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
    author = _get_authenticated_user(collector)
    collection = _collect_personal_activity(collector, repo_input, months, filters, author)

    # Collect detailed feedback
    console.print()
    console.rule("Phase 2: Detailed Feedback Analysis")
    from github_feedback.constants import DAYS_PER_MONTH_APPROX
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


def persist_metrics(output_dir: Path, metrics_data: dict, filename: str = "metrics.json") -> Path:
    """Persist raw metrics to disk for later reporting.

    Args:
        output_dir: Directory to save metrics
        metrics_data: Metrics data to serialize
        filename: Output filename

    Returns:
        Path to saved metrics file

    Raises:
        RuntimeError: If file operations fail
    """
    import json

    output_dir = output_dir.expanduser()

    # Create directory with error handling
    from .utils import FileSystemManager

    try:
        FileSystemManager.ensure_directory(output_dir)
    except PermissionError as exc:
        raise RuntimeError(
            f"Permission denied creating directory {output_dir}: {exc}"
        ) from exc
    except OSError as exc:
        raise RuntimeError(
            f"Failed to create directory {output_dir}: {exc}"
        ) from exc

    metrics_path = output_dir / filename

    # Validate path before writing
    if metrics_path.exists() and not metrics_path.is_file():
        raise RuntimeError(
            f"Cannot write to {metrics_path}: path exists but is not a file"
        )

    # Write metrics with error handling
    try:
        with metrics_path.open("w", encoding="utf-8") as handle:
            json.dump(metrics_data, handle, indent=2)
    except PermissionError as exc:
        raise RuntimeError(
            f"Permission denied writing to {metrics_path}: {exc}"
        ) from exc
    except OSError as exc:
        if exc.errno == 28:  # ENOSPC - No space left on device
            raise RuntimeError(
                f"No space left on device while writing to {metrics_path}"
            ) from exc
        raise RuntimeError(
            f"Failed to write metrics to {metrics_path}: {exc}"
        ) from exc
    except (TypeError, ValueError) as exc:
        raise RuntimeError(
            f"Failed to serialize metrics data: {exc}"
        ) from exc

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

    _print_config_summary()


def _print_config_summary() -> None:
    """Render the current configuration in either table or plain format."""

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
        console.print_error(exc)
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
        console.print_error(exc)
        raise typer.Exit(code=1) from exc


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
    try:
        config = Config.load()

        if action == "list":
            if not config.server.custom_enterprise_hosts:
                console.print("[info]No custom enterprise hosts saved.[/]")
                console.print("[dim]Add hosts using:[/] gfa config hosts add <host-url>")
            else:
                console.print("[accent]Custom Enterprise Hosts:[/]\n")
                for idx, saved_host in enumerate(config.server.custom_enterprise_hosts, 1):
                    console.print(f"  {idx}. {saved_host}")

        elif action == "add":
            if not host:
                console.print("[danger]Error:[/] Host URL is required for 'add' action")
                console.print("[info]Usage:[/] gfa config hosts add <host-url>")
                raise typer.Exit(code=1)

            # Validate and normalize host
            host = host.strip()
            if not host.startswith(("http://", "https://")):
                host = f"https://{host}"

            try:
                validate_url(host, "Enterprise host")
            except ValueError as exc:
                console.print_validation_error(str(exc))
                raise typer.Exit(code=1) from exc

            host = host.rstrip("/")

            if host in config.server.custom_enterprise_hosts:
                console.print(f"[warning]Host '{host}' is already in your custom list[/]")
            else:
                config.server.custom_enterprise_hosts.append(host)
                config.dump()
                console.print(f"[success]✓ Added '{host}' to your custom host list[/]")

        elif action == "remove":
            if not host:
                console.print("[danger]Error:[/] Host URL is required for 'remove' action")
                console.print("[info]Usage:[/] gfa config hosts remove <host-url>")
                raise typer.Exit(code=1)

            # Normalize host for comparison
            host = host.strip().rstrip("/")
            if not host.startswith(("http://", "https://")):
                host = f"https://{host}"

            if host in config.server.custom_enterprise_hosts:
                config.server.custom_enterprise_hosts.remove(host)
                config.dump()
                console.print(f"[success]✓ Removed '{host}' from your custom host list[/]")
            else:
                console.print(f"[warning]Host '{host}' not found in your custom list[/]")
                console.print("[info]Use 'gfa config hosts list' to see saved hosts[/]")

        else:
            console.print_error(f"Unknown action '{action}'")
            console.print("[info]Valid actions:[/] list, add, remove")
            raise typer.Exit(code=1)

    except ValueError as exc:
        console.print_error(exc)
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


@app.command(name="clear-cache")
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


# Keep show-config as a deprecated alias for backward compatibility
@app.command(name="show-config", hidden=True, deprecated=True)
def show_config_deprecated() -> None:
    """Display current configuration settings (deprecated: use 'gfa config show')."""
    console.print("[warning]Note:[/] 'gfa show-config' is deprecated. Use 'gfa config show' instead.")
    console.print()
    _print_config_summary()
