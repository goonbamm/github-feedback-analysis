"""Base classes for section builders."""

from typing import Any, Callable, List

from ..core.models import MetricSnapshot


class MarkdownSectionBuilder:
    """Helper class for building markdown sections with common patterns."""

    @staticmethod
    def build_section(
        title: str,
        description: str = "",
        emoji: str = ""
    ) -> List[str]:
        """Build a section header with optional description."""
        lines = []
        header = f"### {emoji} {title}" if emoji else f"### {title}"
        lines.append(header)
        lines.append("")

        if description:
            lines.append(f"> {description}")
            lines.append("")

        return lines

    @staticmethod
    def build_table(headers: List[str], rows: List[List[str]]) -> List[str]:
        """Build a markdown table from headers and rows."""
        lines = []
        lines.append("| " + " | ".join(headers) + " |")
        lines.append("|" + "|".join(["---"] * len(headers)) + "|")

        for row in rows:
            lines.append("| " + " | ".join(str(cell) for cell in row) + " |")

        lines.append("")
        return lines

    @staticmethod
    def build_list(items: List[str], prefix: str = "-") -> List[str]:
        """Build a markdown list from items."""
        return [f"{prefix} {item}" for item in items] + [""]

    @staticmethod
    def build_subsection(
        data_check: Any,
        title: str,
        content_builder: Callable[[], List[str]],
        emoji: str = "",
        description: str = ""
    ) -> List[str]:
        """Build a subsection if data exists, using a content builder function."""
        lines = []
        if data_check:
            lines.extend(MarkdownSectionBuilder.build_section(title, description, emoji))
            lines.extend(content_builder())
        return lines


class SectionBuilder:
    """Base class for all section builders."""

    def __init__(self, metrics: MetricSnapshot):
        """Initialize builder with metrics data.

        Args:
            metrics: MetricSnapshot containing all analysis data
        """
        self.metrics = metrics
        self.md = MarkdownSectionBuilder()

    def build(self) -> List[str]:
        """Build and return section content.

        Returns:
            List of markdown lines for this section
        """
        raise NotImplementedError("Subclasses must implement build()")
