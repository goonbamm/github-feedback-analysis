"""Display and rendering functions for CLI output."""

from pathlib import Path
from typing import List, Optional, Tuple

try:
    from rich import box
    from rich.align import Align
    from rich.columns import Columns
    from rich.console import Group
    from rich.panel import Panel
    from rich.rule import Rule
    from rich.table import Table
    from rich.text import Text
except ModuleNotFoundError:
    Align = None
    Columns = None
    Group = None
    Panel = None
    Rule = None
    Table = None
    Text = None
    box = None

from ...console import Console
from ...models import AnalysisStatus, MetricSnapshot


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


def display_final_summary(
    author: str,
    repo_input: str,
    pr_results: list,
    integrated_report_path: Optional[Path],
    artifacts: List[Tuple[str, Path]],
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
