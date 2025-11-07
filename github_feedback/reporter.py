"""Report generation for GitHub feedback analysis."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

try:  # pragma: no cover - optional dependency
    from fpdf import FPDF
except ModuleNotFoundError:  # pragma: no cover - fallback when fpdf is missing
    FPDF = None  # type: ignore

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

    def generate_pdf(self, metrics: MetricSnapshot) -> Path:
        """Create a minimal PDF artefact from the markdown summary."""

        self.ensure_structure()
        pdf_path = self.output_dir / "report.pdf"

        if FPDF is None:  # pragma: no cover - exercised when dependency missing
            pdf_path.write_text(
                "GitHub Feedback Report\n"
                f"Repository: {metrics.repo}\n"
                f"Period: {metrics.months} months\n"
            )
            console.log(
                "PDF dependency missing; wrote placeholder text file",
                f"path={pdf_path}",
            )
            return pdf_path

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)

        pdf.multi_cell(0, 10, txt=f"GitHub Feedback Report: {metrics.repo}")
        pdf.ln(4)
        pdf.multi_cell(0, 10, txt=f"Period: {metrics.months} months")
        pdf.ln(4)

        pdf.set_font("Arial", style="B", size=12)
        pdf.cell(0, 10, txt="Summary", ln=1)
        pdf.set_font("Arial", size=11)
        for key, value in metrics.summary.items():
            pdf.multi_cell(0, 8, txt=f"{key.title()}: {value}")

        pdf.ln(4)
        pdf.set_font("Arial", style="B", size=12)
        pdf.cell(0, 10, txt="Metrics", ln=1)
        pdf.set_font("Arial", size=11)
        for domain, domain_stats in metrics.stats.items():
            pdf.multi_cell(0, 8, txt=domain.title())
            for stat_name, stat_value in domain_stats.items():
                if isinstance(stat_value, (int, float)):
                    text_value = f"{stat_value:.2f}"
                else:
                    text_value = str(stat_value)
                pdf.multi_cell(
                    0,
                    8,
                    txt=f"  - {stat_name.replace('_', ' ').title()}: {text_value}",
                )
            pdf.ln(2)

        pdf.ln(4)
        pdf.set_font("Arial", style="B", size=12)
        pdf.cell(0, 10, txt="Evidence", ln=1)
        pdf.set_font("Arial", size=11)
        for domain, links in metrics.evidence.items():
            pdf.multi_cell(0, 8, txt=domain.title())
            for link in links:
                pdf.multi_cell(0, 8, txt=f"  - {link}")
            pdf.ln(2)

        pdf.output(str(pdf_path))
        console.log("Writing PDF report", f"path={pdf_path}")
        return pdf_path

    def generate_templates(self) -> Sequence[Path]:
        """Create recommended repository templates."""

        self.ensure_structure()
        template_dir = Path("templates")
        template_dir.mkdir(parents=True, exist_ok=True)

        templates = {
            "pull_request_template.md": self._render_template(
                "### Summary\n\n- _Describe the change._\n\n### Testing\n\n- _List the tests executed._\n"
            ),
            "REVIEW_GUIDE.md": self._render_template(
                "# Review Guide\n\n1. Verify test coverage.\n2. Validate architectural alignment.\n3. Assess documentation updates.\n"
            ),
            "CONTRIBUTING.md": self._render_template(
                "# Contributing\n\n- Fork the repository and create a feature branch.\n- Run `gf analyze` before submitting a PR.\n- Follow the review guide for expectations.\n"
            ),
        }

        created_paths = []
        for filename, contents in templates.items():
            path = template_dir / filename
            path.write_text(contents, encoding="utf-8")
            created_paths.append(path)
            console.log("Generated template", f"path={path}")
        return created_paths

    @staticmethod
    def _render_template(contents: str) -> str:
        return contents
