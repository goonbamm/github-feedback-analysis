"""Report generation for GitHub feedback analysis."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .console import Console
from .models import MetricSnapshot

console = Console()


@dataclass(slots=True)
class Reporter:
    """Create human-readable artefacts from metrics."""

    output_dir: Path = Path("reports")

    def ensure_structure(self) -> None:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        (self.output_dir / "charts").mkdir(parents=True, exist_ok=True)

    def generate_markdown(self, metrics: MetricSnapshot) -> Path:
        """Create a markdown report for the provided metrics."""

        self.ensure_structure()
        report_path = self.output_dir / "report.md"

        console.log("Writing markdown report", f"path={report_path}")

        summary_lines = ["# GitHub Feedback Report", ""]
        summary_lines.append(f"Repository: **{metrics.repo}**")
        summary_lines.append(f"Period: **{metrics.months} months**")
        summary_lines.append("")
        summary_lines.append("## Summary")

        for key, value in metrics.summary.items():
            summary_lines.append(f"- **{key.title()}**: {value}")

        summary_lines.append("")
        summary_lines.append("## Metrics")

        for domain, domain_stats in metrics.stats.items():
            summary_lines.append(f"### {domain.title()}")
            for stat_name, stat_value in domain_stats.items():
                if isinstance(stat_value, (int, float)):
                    summary_lines.append(
                        f"- {stat_name.replace('_', ' ').title()}: {stat_value:.2f}"
                    )
                else:
                    summary_lines.append(
                        f"- {stat_name.replace('_', ' ').title()}: {stat_value}"
                    )
            summary_lines.append("")

        summary_lines.append("## Evidence")
        for domain, links in metrics.evidence.items():
            summary_lines.append(f"### {domain.title()}")
            for link in links:
                summary_lines.append(f"- {link}")
            summary_lines.append("")

        report_path.write_text("\n".join(summary_lines), encoding="utf-8")
        return report_path

