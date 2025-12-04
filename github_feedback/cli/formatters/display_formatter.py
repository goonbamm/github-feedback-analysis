"""Display formatting utilities for CLI output."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, List, Optional

if TYPE_CHECKING:
    from github_feedback.console import Console

try:
    from rich import box
    from rich.table import Table
except ModuleNotFoundError:
    Table = None
    box = None

from github_feedback import cli_helpers


def print_config_summary(console: Console) -> None:
    """Render the current configuration in either table or plain format.

    Args:
        console: Console instance for output
    """
    config = cli_helpers.load_config()
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


def display_final_summary(
    console: Console,
    author: str,
    repo_input: str,
    pr_results: list,
    integrated_report_path: Optional[Path],
    artifacts: List[tuple[str, Path]],
) -> None:
    """Display final summary of the analysis.

    Args:
        console: Console instance for output
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
