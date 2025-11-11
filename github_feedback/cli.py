"""Command line interface for the GitHub feedback toolkit."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import List, Optional

import typer
from typer.models import OptionInfo

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

app = typer.Typer(help="Analyze GitHub repositories and generate feedback reports.")
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
        return Config.load()
    except ValueError as exc:
        console.print(f"[danger]Configuration error:[/] {exc}")
        console.print("[info]Hint:[/] Run [accent]gf init[/] to set up your configuration")
        raise typer.Exit(code=1) from exc


@app.command()
def init(
    pat: str = typer.Option(
        ...,
        prompt="GitHub Personal Access Token",
        hide_input=True,
        help="GitHub Personal Access Token (requires 'repo' scope for private repos)",
    ),
    months: int = typer.Option(12, help="Default analysis window in months"),
    enterprise_host: Optional[str] = typer.Option(
        "",
        prompt="GitHub Enterprise host (leave empty for github.com)",
        help=(
            "Base URL of your GitHub Enterprise host (e.g. https://github.example.com). "
            "When provided, API, GraphQL, and web URLs are derived automatically."
        ),
    ),
    llm_endpoint: str = typer.Option(
        ...,
        prompt="LLM API endpoint (OpenAI-compatible format)",
        help="LLM endpoint URL (e.g. http://localhost:8000/v1/chat/completions)",
    ),
    llm_model: str = typer.Option(
        ...,
        prompt="LLM model name (e.g. gpt-4, claude-3-5-sonnet-20241022)",
        help="Model identifier for the LLM",
    ),
) -> None:
    """Initialize configuration and store credentials securely.

    This command sets up your GitHub access token, LLM endpoint, and other
    configuration options. Run this once before using other commands.
    """

    host_input = (enterprise_host or "").strip()
    if host_input:
        host = host_input
        if not host.startswith(("http://", "https://")):
            host = f"https://{host}"
        host = host.rstrip("/")
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
    config.dump()
    console.print("[success]Configuration saved successfully.[/]")

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
            Align.center(Text("Insights Ready", style="title")),
            Align.center(Text(metrics.repo, style="repo")),
            Align.center(Text(f"{metrics.months} month retrospection", style="muted")),
        ),
        border_style="accent",
        padding=(1, 4),
    )

    console.print(header)
    console.print(
        Rule(
            title=f"[{status_style}]Status • {metrics.status.value.upper()}[/]",
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

        summary_panel = Panel(summary_grid, border_style="frame", title="Pulse Check", title_align="left")
    else:
        summary_panel = Panel(Text("No summary metrics available", style="muted"), border_style="frame")

    stat_panels = []
    for domain, domain_stats in metrics.stats.items():
        stat_table = Table(
            box=box.MINIMAL,
            show_edge=False,
            pad_edge=False,
            expand=True,
        )
        stat_table.add_column("Metric", style="label")
        stat_table.add_column("Value", style="value")
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
        highlights_panel = Panel(highlights_text, title="Momentum Highlights", border_style="frame")
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
        console.print(Panel(awards_text, title="Awards Cabinet", border_style="accent"))

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
) -> Optional[DetailedFeedbackSnapshot]:
    """Collect and analyze detailed feedback data."""
    from concurrent.futures import ThreadPoolExecutor, as_completed
    from .llm import LLMClient

    console.print("[accent]Collecting detailed feedback data...", style="accent")

    try:
        # Collect detailed data in parallel
        data_collection_tasks = {
            "commits": (collector.collect_commit_messages, (repo, since, filters), {"limit": 100}, "commit messages"),
            "pr_titles": (collector.collect_pr_titles, (repo, since, filters), {"limit": 100}, "PR titles"),
            "review_comments": (collector.collect_review_comments_detailed, (repo, since, filters), {"limit": 100}, "review comments"),
            "issues": (collector.collect_issue_details, (repo, since, filters), {"limit": 100}, "issues"),
        }

        collected_data = {}
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {
                executor.submit(func, *args, **kwargs): (key, label)
                for key, (func, args, kwargs, label) in data_collection_tasks.items()
            }

            completed = 0
            total = len(futures)
            for future in as_completed(futures):
                key, label = futures[future]
                try:
                    collected_data[key] = future.result()
                    completed += 1
                    console.print(f"[success]✓ {label} collected ({completed}/{total})", style="success")
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
            for future in as_completed(futures):
                key, label = futures[future]
                try:
                    results[key] = future.result()
                    completed += 1
                    console.print(f"[success]✓ {label} analyzed ({completed}/{total})", style="success")
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
        console.print("[info]Continuing with standard analysis...", style="info")
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

    if metrics.detailed_feedback:
        metrics_payload["detailed_feedback"] = metrics.detailed_feedback.to_dict()

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

    # Generate prompt packets
    prompt_artifacts = reporter.generate_prompt_packets(metrics)
    for prompt_request, prompt_path in prompt_artifacts:
        artifacts.append((f"Prompt • {prompt_request.title}", prompt_path))

    return artifacts


@app.command()
def brief(
    repo: str = typer.Option(
        "",
        "--repo",
        prompt="Repository to analyze (e.g. torvalds/linux)",
        help="Repository in owner/name format (e.g. microsoft/vscode)",
    ),
) -> None:
    """Analyze repository activity and generate detailed reports.

    This command collects commits, PRs, reviews, and issues from a GitHub
    repository, then generates comprehensive reports with insights and
    recommendations. Reports are saved to the 'reports/' directory.
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
        console.print("[info]Hint:[/] Check your GitHub token with [accent]gf show-config[/]")
        raise typer.Exit(code=1) from exc

    analyzer = Analyzer(web_base_url=config.server.web_url)
    output_dir = _resolve_output_dir(Path("reports"))
    reporter = Reporter(output_dir=output_dir)

    repo_input = repo.strip()
    if not repo_input:
        console.print("[danger]Error:[/] Repository value cannot be empty")
        console.print("[info]Expected format:[/] [accent]owner/repository[/]")
        console.print("[info]Example:[/] [accent]gf brief --repo torvalds/linux[/]")
        raise typer.Exit(code=1)

    # Phase 1: Collect repository data
    with console.status("[accent]Collecting repository signals...", spinner="bouncingBar"):
        collection = collector.collect(repo=repo_input, months=months, filters=filters)

    # Phase 2: Collect detailed feedback
    since = datetime.now(timezone.utc) - timedelta(days=30 * max(months, 1))
    detailed_feedback_snapshot = _collect_detailed_feedback(
        collector, analyzer, config, repo_input, since, filters
    )

    # Phase 2.5: Collect year-end review data in parallel
    from concurrent.futures import ThreadPoolExecutor, as_completed

    console.print("[accent]Collecting year-end review data in parallel...", style="accent")

    # Get PR metadata once for reuse
    _, pr_metadata = collector._list_pull_requests(repo_input, since, filters)

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
        for future in as_completed(futures):
            key, label = futures[future]
            try:
                yearend_data[key] = future.result()
                completed += 1
                console.print(f"[success]✓ {label} collected ({completed}/{total})", style="success")
            except Exception as exc:
                console.print(f"[warning]✗ {label} collection failed: {exc}", style="warning")
                yearend_data[key] = None

    monthly_trends_data = yearend_data.get("monthly_trends")
    tech_stack_data = yearend_data.get("tech_stack")
    collaboration_data = yearend_data.get("collaboration")

    # Phase 3: Compute metrics
    with console.status("[accent]Synthesizing insights...", spinner="dots"):
        metrics = analyzer.compute_metrics(
            collection,
            detailed_feedback=detailed_feedback_snapshot,
            monthly_trends_data=monthly_trends_data,
            tech_stack_data=tech_stack_data,
            collaboration_data=collaboration_data,
        )

    # Phase 4: Generate reports
    metrics_payload = _prepare_metrics_payload(metrics)
    artifacts = _generate_artifacts(metrics, reporter, output_dir, metrics_payload)

    # Phase 5: Display results
    console.rule("Analysis Summary")
    _render_metrics(metrics)
    console.rule("Artifacts")
    for label, path in artifacts:
        console.print(f"[success]{label} generated:[/]", f"[value]{path}[/]")

    console.print()
    console.print("[success]✓ Analysis complete![/]")
    console.print()
    console.print("[info]Next steps:[/]")
    console.print("  • View the report: [accent]cat reports/report.md[/]")
    console.print("  • Review your PRs: [accent]gf feedback --repo {}[/]".format(repo_input))




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
def main_callback() -> None:
    """CLI entry-point callback for shared initialisation."""

    pass


@app.command()
def feedback(
    repo: str = typer.Option(
        "",
        "--repo",
        prompt="Repository to review (e.g. myname/myproject)",
        help="Repository in owner/name format (e.g. facebook/react)",
    ),
    state: str = typer.Option(
        "all",
        "--state",
        help="PR state filter: 'open', 'closed', or 'all' (default: all)",
    ),
) -> None:
    """Generate AI-powered reviews for your pull requests.

    This command reviews all PRs authored by you (based on your GitHub token)
    in the specified repository. It analyzes code changes, comments, and
    creates an integrated retrospective report. Reviews are saved to the
    'reviews/' directory.
    """

    config = _load_config()

    try:
        collector = Collector(config)
    except ValueError as exc:
        console.print(f"[danger]Error:[/] {exc}")
        console.print("[info]Hint:[/] Check your configuration with [accent]gf show-config[/]")
        raise typer.Exit(code=1) from exc

    llm_client = LLMClient(
        endpoint=config.llm.endpoint,
        model=config.llm.model,
    )

    reviewer = Reviewer(collector=collector, llm=llm_client)

    repo_input = repo.strip()
    if not repo_input:
        console.print("[danger]Error:[/] Repository value cannot be empty")
        console.print("[info]Expected format:[/] [accent]owner/repository[/]")
        console.print("[info]Example:[/] [accent]gf feedback --repo myname/myproject[/]")
        raise typer.Exit(code=1)

    state_value = state.default if isinstance(state, OptionInfo) else state

    def _render_result(pr_number: int, artefact_path: Path, summary_path: Path, markdown_path: Path) -> None:
        console.print(f"[accent]Pull Request #[/][value]{pr_number}[/]")
        console.print(
            "[success]Pull request artefacts cached:[/]", f"[value]{artefact_path}[/]"
        )
        console.print(
            "[success]Structured summary stored:[/]", f"[value]{summary_path}[/]"
        )
        console.print(
            "[success]Markdown review generated:[/]", f"[value]{markdown_path}[/]"
        )
        console.print("")

    results = []

    # Step 1: Generate PR reviews
    console.rule("Step 1: Generating PR Reviews")

    state_normalised = (state_value or "").lower().strip() or "all"
    if state_normalised not in {"open", "closed", "all"}:
        console.print("State must be one of: open, closed, all.")
        raise typer.Exit(code=1)

    with console.status(
        "[accent]Retrieving authenticated user from PAT...", spinner="dots"
    ):
        try:
            author = collector.get_authenticated_user()
        except (ValueError, PermissionError) as exc:
            console.print(f"[error]Failed to get authenticated user: {exc}[/]")
            raise typer.Exit(code=1) from exc

    with console.status(
        "[accent]Discovering authored pull requests...", spinner="dots"
    ):
        numbers = collector.list_authored_pull_requests(
            repo=repo_input,
            author=author,
            state=state_normalised,
        )

    if not numbers:
        console.print(
            f"[warning]No pull requests found authored by '{author}' in {repo_input}.[/]"
        )
        return

    pr_numbers = sorted(set(numbers))
    total_prs = len(pr_numbers)

    for idx, pr_number in enumerate(pr_numbers, 1):
        with console.status(
            f"[accent]Curating context for PR #{pr_number} ({idx}/{total_prs})...", spinner="line"
        ):
            artefact_path, summary_path, markdown_path = reviewer.review_pull_request(
                repo=repo_input,
                number=pr_number,
            )
        results.append((pr_number, artefact_path, summary_path, markdown_path))
        console.print(f"[success]✓ PR #{pr_number} reviewed ({idx}/{total_prs})", style="success")

    console.rule("Review Assets")
    for pr_number, artefact_path, summary_path, markdown_path in results:
        _render_result(pr_number, artefact_path, summary_path, markdown_path)

    if results:
        review_root_value = getattr(reviewer, "output_dir", Path("reviews"))
        review_root = Path(review_root_value).expanduser().resolve()
        console.print(
            "[info]Review artefacts stored under:[/]",
            f"[value]{review_root}[/]",
        )

    # Step 2: Generate integrated report
    console.rule("Step 2: Generating Integrated Report")

    review_reporter = ReviewReporter(
        output_dir=Path("reviews"),
        llm=llm_client,
    )

    try:
        with console.status("[accent]Creating integrated report...", spinner="dots"):
            report_path = review_reporter.create_integrated_report(repo_input)
    except ValueError as exc:
        console.print(f"[warning]{exc}[/]")
        raise typer.Exit(code=1) from exc

    console.rule("Integrated Review Report")
    console.print(
        "[success]Integrated review report generated:[/]",
        f"[value]{report_path}[/]",
    )

    console.print()
    console.print("[success]✓ Review complete![/]")
    console.print()
    console.print("[info]Next steps:[/]")
    console.print("  • Read the report: [accent]cat {}[/]".format(report_path))
    console.print("  • Analyze the repository: [accent]gf brief --repo {}[/]".format(repo_input))


@app.command()
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
