"""Report generation for GitHub feedback analysis."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import textwrap
from typing import Sequence

try:  # pragma: no cover - optional dependency
    from fpdf import FPDF
    from fpdf.enums import XPos, YPos
except ModuleNotFoundError:  # pragma: no cover - fallback when fpdf is missing
    FPDF = None  # type: ignore
    XPos = YPos = None  # type: ignore

from .console import Console
from .fonts import ensure_hangul_font
from .models import MetricSnapshot

console = Console()

_FONT_FAMILY = "HangulSimplified"


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
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.set_left_margin(15)
        pdf.set_right_margin(15)
        pdf.add_page()
        self._set_pdf_font(pdf, size=12)

        page_width = self._effective_page_width(pdf)

        pdf.multi_cell(
            page_width,
            10,
            text=self._wrap_text_for_pdf(pdf, f"GitHub Feedback Report: {metrics.repo}"),
        )
        pdf.ln(4)
        pdf.multi_cell(
            page_width,
            10,
            text=self._wrap_text_for_pdf(pdf, f"Period: {metrics.months} months"),
        )
        pdf.ln(4)

        self._set_pdf_font(pdf, style="B", size=12)
        pdf.cell(0, 10, text="Summary", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self._set_pdf_font(pdf, size=11)
        for key, value in metrics.summary.items():
            pdf.multi_cell(
                page_width,
                8,
                text=self._wrap_text_for_pdf(pdf, f"{key.title()}: {value}"),
            )

        pdf.ln(4)
        self._set_pdf_font(pdf, style="B", size=12)
        pdf.cell(0, 10, text="Metrics", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self._set_pdf_font(pdf, size=11)
        for domain, domain_stats in metrics.stats.items():
            pdf.multi_cell(
                page_width,
                8,
                text=self._wrap_text_for_pdf(pdf, domain.title()),
            )
            for stat_name, stat_value in domain_stats.items():
                if isinstance(stat_value, (int, float)):
                    text_value = f"{stat_value:.2f}"
                else:
                    text_value = str(stat_value)
                pdf.multi_cell(
                    page_width,
                    8,
                    text=self._wrap_text_for_pdf(
                        pdf,
                        f"  - {stat_name.replace('_', ' ').title()}: {text_value}",
                    ),
                )
            pdf.ln(2)

        pdf.ln(4)
        self._set_pdf_font(pdf, style="B", size=12)
        pdf.cell(0, 10, text="Evidence", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self._set_pdf_font(pdf, size=11)
        for domain, links in metrics.evidence.items():
            pdf.multi_cell(
                page_width,
                8,
                text=self._wrap_text_for_pdf(pdf, domain.title()),
            )
            for link in links:
                pdf.multi_cell(
                    page_width,
                    8,
                    text=self._wrap_text_for_pdf(pdf, f"  - {link}"),
                )
            pdf.ln(2)

        pdf.output(str(pdf_path))
        console.log("Writing PDF report", f"path={pdf_path}")
        return pdf_path

    @staticmethod
    def _effective_page_width(pdf: "FPDF") -> float:
        """Return the writable page width for the provided PDF instance."""

        return pdf.w - pdf.l_margin - pdf.r_margin

    def _wrap_text_for_pdf(self, pdf: "FPDF", text: str) -> str:
        """Insert line breaks so FPDF can render long tokens safely."""

        effective_width = max(int(self._effective_page_width(pdf)), 1)
        reference_width = pdf.get_string_width("M") or 1
        max_chars = max(int(effective_width / reference_width), 1)

        wrapped_lines: list[str] = []
        lines = text.splitlines() or [""]
        for raw_line in lines:
            if not raw_line:
                wrapped_lines.append("")
                continue

            leading_spaces = len(raw_line) - len(raw_line.lstrip(" "))
            indent = raw_line[:leading_spaces]
            content = raw_line[leading_spaces:]
            available_chars = max(max_chars - leading_spaces, 1)

            wrapper = textwrap.TextWrapper(
                width=available_chars,
                break_long_words=True,
                break_on_hyphens=True,
                drop_whitespace=False,
                replace_whitespace=False,
            )

            wrapped = wrapper.fill(content)
            wrapped_lines.extend(f"{indent}{segment}" for segment in wrapped.split("\n"))

        return "\n".join(wrapped_lines)

    def _set_pdf_font(self, pdf: "FPDF", *, style: str = "", size: int = 12) -> None:
        """Register and activate the bundled Hangul-safe font."""

        font_style = style.upper()
        font_path = ensure_hangul_font()
        font_key = f"{_FONT_FAMILY.lower()}{font_style}" if font_style else _FONT_FAMILY.lower()
        if font_key not in pdf.fonts:
            pdf.add_font(_FONT_FAMILY, style=font_style, fname=str(font_path))

        pdf.set_font(_FONT_FAMILY, style=font_style, size=size)

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
