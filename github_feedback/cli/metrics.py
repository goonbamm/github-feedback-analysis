"""Metrics computation, display, and persistence utilities for CLI."""

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional

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
from ..core.console import Console
from ..core.models import AnalysisStatus, DetailedFeedbackSnapshot, MetricSnapshot

console = Console()


def render_metrics(metrics: MetricSnapshot) -> None:
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


def prepare_metrics_payload(metrics: MetricSnapshot) -> dict:
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

    # Add witch critique
    if metrics.witch_critique:
        metrics_payload["witch_critique"] = metrics.witch_critique.to_dict()

    return metrics_payload


def compute_and_display_metrics(
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
    render_metrics(metrics)

    return metrics


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
    output_dir = output_dir.expanduser()

    # Create directory with error handling
    from ..core.utils import FileSystemManager

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
