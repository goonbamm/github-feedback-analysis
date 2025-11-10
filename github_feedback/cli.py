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
from .llm import LLMClient
from .models import AnalysisFilters, AnalysisStatus, MetricSnapshot
from .reporter import Reporter
from .reviewer import Reviewer

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
    enterprise_host: Optional[str] = typer.Option(
        "",
        prompt="GitHub Enterprise host (press enter for github.com)",
        help=(
            "Base URL of your GitHub Enterprise host (e.g. https://github.example.com). "
            "When provided, API, GraphQL, and web URLs are derived automatically."
        ),
    ),
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

    host_input = (enterprise_host or "").strip()
    if host_input:
        host = host_input
        if not host.startswith(("http://", "https://")):
            host = f"https://{host}"
        host = host.rstrip("/")
        api_url = f"{host}/api/v3"
        graphql_url = f"{host}/api/graphql"
        web_url = host

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
    repo: str = typer.Option(
        "",
        "--repo",
        prompt="Repository to analyse (owner/name)",
        help="Repository in owner/name format",
    ),
    months: Optional[int] = typer.Option(None, help="Number of months to analyse"),
    include_branch: Optional[str] = typer.Option(None, help="Branch to include"),
    exclude_branch: Optional[str] = typer.Option(None, help="Branch to exclude"),
    include_path: Optional[str] = typer.Option(None, help="Path prefix to include"),
    exclude_path: Optional[str] = typer.Option(None, help="Path prefix to exclude"),
    include_language: Optional[str] = typer.Option(None, help="File extension to include"),
    include_bots: bool = typer.Option(False, help="Include bot commits in the analysis"),
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

    repo_input = repo.strip()
    if not repo_input:
        console.print("Repository value cannot be empty.")
        raise typer.Exit(code=1)

    collection = collector.collect(repo=repo_input, months=months, filters=filters)
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

    persist_metrics(Path("reports") / "metrics.json", metrics_payload)

    markdown_path = reporter.generate_markdown(metrics)
    console.print("Markdown report generated:", markdown_path)


@app.command()
def report() -> None:
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
        highlights=payload.get("highlights", []),
        spotlight_examples=payload.get("spotlight_examples", {}),
        yearbook_story=payload.get("yearbook_story", []),
        awards=payload.get("awards", []),
    )

    reporter = Reporter()
    reporter.generate_markdown(metrics)

    console.print("Report regeneration complete.")


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

    artefact_path, summary_path, markdown_path = reviewer.review_pull_request(
        repo=repo_input,
        number=number,
    )

    console.print("Pull request artefacts cached:", artefact_path)
    console.print("Structured summary stored:", summary_path)
    console.print("Markdown review generated:", markdown_path)
