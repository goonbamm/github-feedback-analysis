"""Metrics preparation and persistence utilities."""

import json
from pathlib import Path
from typing import Optional

from ...models import MetricSnapshot


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

    return metrics_payload


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
    from ...utils import FileSystemManager

    output_dir = output_dir.expanduser()

    # Create directory with error handling
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
