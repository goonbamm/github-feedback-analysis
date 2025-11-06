"""Command line interface for the GitHub feedback toolkit."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Optional

import typer

try:  # pragma: no cover - optional rich dependency
    from rich import box
    from rich.table import Table
except ModuleNotFoundError:  # pragma: no cover - fallback when rich is missing
    Table = None
    box = None

from .analyzer import Analyzer
from .collector import Collector
from .config import Config
from .console import Console
from .models import AnalysisFilters, AnalysisStatus, MetricSnapshot
from .reporter import Reporter

app = typer.Typer(help="Analyze GitHub repositories and generate feedback reports.")
console = Console()


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
    api_url: str = typer.Option(
        "https://api.github.com", help="Base REST API URL (set to your Enterprise host if needed)"
    ),
    graphql_url: str = typer.Option(
        "https://api.github.com/graphql",
        help="GraphQL endpoint URL (Enterprise: https://<host>/api/graphql)",
    ),
    web_url: str = typer.Option(
        "https://github.com", help="Web URL used when generating evidence links"
    ),
    verify_ssl: bool = typer.Option(
        True, help="Verify HTTPS certificates when calling the GitHub API"
    ),
    llm_endpoint: str = typer.Option(
        "http://localhost:8000/v1/chat/completions", help="Default LLM endpoint"
    ),
    llm_model: str = typer.Option("", help="Preferred model identifier for the LLM"),
) -> None:
    """Initialise local configuration and store credentials securely."""

    config = Config.load()
    config.update_auth(pat)
    config.server.api_url = api_url
    config.server.graphql_url = graphql_url
    config.server.web_url = web_url
    config.server.verify_ssl = verify_ssl
    config.llm.endpoint = llm_endpoint
    config.llm.model = llm_model
    config.defaults.months = months
    config.dump()
    console.print("Configuration saved successfully.")


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

    table = Table(title="GitHub Feedback Configuration", box=box.SIMPLE_HEAVY)
    table.add_column("Section")
    table.add_column("Values")

    for section, values in data.items():
        table.add_row(section, "\n".join(f"{k}: {v}" for k, v in values.items()))

    console.print(table)


@app.command()
def analyze(
    repo: str = typer.Option(..., "--repo", help="Repository in owner/name format"),
    months: Optional[int] = typer.Option(None, help="Number of months to analyse"),
    include_branch: Optional[str] = typer.Option(None, help="Branch to include"),
    exclude_branch: Optional[str] = typer.Option(None, help="Branch to exclude"),
    include_path: Optional[str] = typer.Option(None, help="Path prefix to include"),
    exclude_path: Optional[str] = typer.Option(None, help="Path prefix to exclude"),
    include_language: Optional[str] = typer.Option(None, help="File extension to include"),
    include_bots: bool = typer.Option(False, help="Include bot commits in the analysis"),
    generate_pdf: bool = typer.Option(True, help="Also generate a PDF report"),
) -> None:
    """Collect data, compute metrics, and generate reports."""

    config = _load_config()
    months = months or config.defaults.months
    filters = AnalysisFilters(
        include_branches=[include_branch] if include_branch else [],
        exclude_branches=[exclude_branch] if exclude_branch else [],
        include_paths=[include_path] if include_path else [],
        exclude_paths=[exclude_path] if exclude_path else [],
        include_languages=[include_language] if include_language else [],
        exclude_bots=not include_bots,
    )

    try:
        collector = Collector(config)
    except ValueError as exc:
        console.print(str(exc))
        raise typer.Exit(code=1) from exc

    analyzer = Analyzer(web_base_url=config.server.web_url)
    reporter = Reporter()

    collection = collector.collect(repo=repo, months=months, filters=filters)
    metrics = analyzer.compute_metrics(collection)

    metrics_payload = {
        "repo": metrics.repo,
        "months": metrics.months,
        "generated_at": metrics.generated_at.isoformat(),
        "status": metrics.status.value,
        "summary": metrics.summary,
        "stats": metrics.stats,
        "evidence": metrics.evidence,
    }

    persist_metrics(Path("reports") / "metrics.json", metrics_payload)

    markdown_path = reporter.generate_markdown(metrics)
    console.print("Markdown report generated:", markdown_path)

    if generate_pdf:
        pdf_path = reporter.generate_pdf(metrics)
        console.print("PDF report generated:", pdf_path)


@app.command()
def report(
    formats: str = typer.Option("md,pdf", help="Comma separated list of output formats"),
) -> None:
    """Generate reports from the latest cached metrics."""

    metrics_file = Path("reports") / "metrics.json"
    if not metrics_file.exists():
        console.print("No cached metrics available. Run `gf analyze` first.")
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
    )

    reporter = Reporter()
    formats_list = [fmt.strip().lower() for fmt in formats.split(",") if fmt.strip()]
    if "md" in formats_list:
        reporter.generate_markdown(metrics)
    if "pdf" in formats_list:
        reporter.generate_pdf(metrics)

    console.print("Report regeneration complete.")


@app.command()
def suggest_templates() -> None:
    """Create recommended repository templates in the local directory."""

    reporter = Reporter()
    paths = reporter.generate_templates()
    for path in paths:
        console.print("Template created:", path)


def persist_metrics(metrics_path: Path, metrics_data: dict) -> None:
    """Persist raw metrics to disk for later reporting."""

    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    import json

    with metrics_path.open("w", encoding="utf-8") as handle:
        json.dump(metrics_data, handle, indent=2)


@app.callback()
def main_callback() -> None:
    """CLI entry-point callback for shared initialisation."""

    pass
