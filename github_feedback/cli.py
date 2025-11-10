"""Command line interface for the GitHub feedback toolkit."""

from __future__ import annotations

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
from .models import AnalysisFilters, AnalysisStatus, MetricSnapshot
from .reporter import Reporter
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
        console.print("Configuration error:", exc)
        raise typer.Exit(code=1) from exc


@app.command()
def init(
    pat: str = typer.Option(..., prompt=True, hide_input=True, help="GitHub Personal Access Token"),
    months: int = typer.Option(12, help="Default analysis window in months"),
    enterprise_host: Optional[str] = typer.Option(
        "",
        prompt="GitHub Enterprise host (press enter for github.com)",
        help=(
            "Base URL of your GitHub Enterprise host (e.g. https://github.example.com). "
            "When provided, API, GraphQL, and web URLs are derived automatically."
        ),
    ),
    llm_endpoint: str = typer.Option(
        ...,
        prompt="LLM endpoint (e.g. http://localhost:8000/v1/chat/completions)",
        help="Default LLM endpoint",
    ),
    llm_model: str = typer.Option(
        ...,
        prompt="LLM model identifier",
        help="Preferred model identifier for the LLM",
    ),
) -> None:
    """Initialise local configuration and store credentials securely."""

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


@app.command()
def show_config() -> None:
    """Display the currently stored configuration (safely)."""

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
            title=f"Status • {metrics.status.value.upper()}",
            style="divider",
            characters="━",
            align="center",
            title_style=status_style,
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


@app.command()
def analyze(
    repo: str = typer.Option(
        "",
        "--repo",
        prompt="Repository to analyse (owner/name)",
        help="Repository in owner/name format",
    ),
    months: Optional[int] = typer.Option(None, help="Number of months to analyse"),
    include_branch: Optional[List[str]] = typer.Option(
        None, help="Branch name to include (repeat for multiple branches)"
    ),
    exclude_branch: Optional[List[str]] = typer.Option(
        None, help="Branch name to exclude (repeat for multiple branches)"
    ),
    include_path: Optional[List[str]] = typer.Option(
        None, help="Path prefix to include (repeat for multiple paths)"
    ),
    exclude_path: Optional[List[str]] = typer.Option(
        None, help="Path prefix to exclude (repeat for multiple paths)"
    ),
    include_language: Optional[List[str]] = typer.Option(
        None, help="File extension to include (repeat for multiple extensions)"
    ),
    include_bots: bool = typer.Option(False, help="Include bot commits in the analysis"),
    html: bool = typer.Option(
        False,
        "--html",
        help="Generate an HTML report alongside the default markdown output.",
    ),
    output_dir: Path = typer.Option(
        Path("reports"),
        "--output-dir",
        path_type=Path,
        help="Directory to store metrics snapshots and generated reports.",
    ),
) -> None:
    """Collect data, compute metrics, and generate reports."""

    config = _load_config()
    months = months or config.defaults.months
    filters = AnalysisFilters(
        include_branches=list(include_branch or []),
        exclude_branches=list(exclude_branch or []),
        include_paths=list(include_path or []),
        exclude_paths=list(exclude_path or []),
        include_languages=list(include_language or []),
        exclude_bots=not include_bots,
    )

    try:
        collector = Collector(config)
    except ValueError as exc:
        console.print(str(exc))
        raise typer.Exit(code=1) from exc

    analyzer = Analyzer(web_base_url=config.server.web_url)
    output_dir = _resolve_output_dir(output_dir)
    reporter = Reporter(output_dir=output_dir)

    repo_input = repo.strip()
    if not repo_input:
        console.print("Repository value cannot be empty.")
        raise typer.Exit(code=1)

    with console.status("[accent]Collecting repository signals...", spinner="bouncingBar"):
        collection = collector.collect(repo=repo_input, months=months, filters=filters)

    with console.status("[accent]Synthesizing insights...", spinner="dots"):
        metrics = analyzer.compute_metrics(collection)

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

    metrics_path = persist_metrics(output_dir=output_dir, metrics_data=metrics_payload)

    artifacts = [("Metrics snapshot", metrics_path)]

    markdown_path = reporter.generate_markdown(metrics)
    artifacts.append(("Markdown report", markdown_path))

    if html:
        artifacts.append(("HTML report", reporter.generate_html(metrics)))
    console.rule("Analysis Summary")
    _render_metrics(metrics)
    console.rule("Artifacts")
    for label, path in artifacts:
        console.print(f"[success]{label} generated:[/]", f"[value]{path}[/]")


@app.command()
def report(
    html: bool = typer.Option(
        False,
        "--html",
        help="Generate an HTML report alongside the cached markdown output.",
    ),
    output_dir: Path = typer.Option(
        Path("reports"),
        "--output-dir",
        path_type=Path,
        help="Directory containing cached metrics and where refreshed reports will be written.",
    ),
) -> None:
    """Generate reports from the latest cached metrics."""

    output_dir = _resolve_output_dir(output_dir)
    metrics_file = output_dir / "metrics.json"
    if not metrics_file.exists():
        console.print("[warning]No cached metrics available.[/] Run `gf analyze` first.")
        raise typer.Exit(code=1)

    import json

    with metrics_file.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)

    metrics = MetricSnapshot(
        repo=payload["repo"],
        months=payload["months"],
        generated_at=datetime.fromisoformat(payload["generated_at"]),
        status=AnalysisStatus(payload.get("status", AnalysisStatus.ANALYSED.value)),
        summary=payload.get("summary", {}),
        stats=payload.get("stats", {}),
        evidence=payload.get("evidence", {}),
        highlights=payload.get("highlights", []),
        spotlight_examples=payload.get("spotlight_examples", {}),
        yearbook_story=payload.get("yearbook_story", []),
        awards=payload.get("awards", []),
    )

    reporter = Reporter(output_dir=output_dir)
    markdown_path = reporter.generate_markdown(metrics)
    artifacts = [("Markdown report", markdown_path)]

    if html:
        html_path = reporter.generate_html(metrics)
        artifacts.append(("HTML report", html_path))

    console.rule("Cached Insights")
    _render_metrics(metrics)
    console.rule("Artifacts")
    for label, path in artifacts:
        console.print(f"[success]{label} refreshed:[/]", f"[value]{path}[/]")


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
def review(
    repo: str = typer.Option(
        "",
        "--repo",
        prompt="Repository to review (owner/name)",
        help="Repository in owner/name format",
    ),
    number: int = typer.Option(
        ..., "--number", prompt="Pull request number", help="Pull request number"
    ),
) -> None:
    """Collect pull request context and generate an LLM powered review."""

    config = _load_config()

    try:
        collector = Collector(config)
    except ValueError as exc:
        console.print(str(exc))
        raise typer.Exit(code=1) from exc

    llm_client = LLMClient(
        endpoint=config.llm.endpoint,
        model=config.llm.model,
    )

    reviewer = Reviewer(collector=collector, llm=llm_client)

    repo_input = repo.strip()
    if not repo_input:
        console.print("Repository value cannot be empty.")
        raise typer.Exit(code=1)

    with console.status("[accent]Curating pull request context...", spinner="line"):
        artefact_path, summary_path, markdown_path = reviewer.review_pull_request(
            repo=repo_input,
            number=number,
        )

    console.rule("Review Assets")
    console.print("[success]Pull request artefacts cached:[/]", f"[value]{artefact_path}[/]")
    console.print("[success]Structured summary stored:[/]", f"[value]{summary_path}[/]")
    console.print("[success]Markdown review generated:[/]", f"[value]{markdown_path}[/]")
