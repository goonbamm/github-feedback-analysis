"""Tests for the markdown reporter outputs."""

from __future__ import annotations

from datetime import datetime

import pytest

from github_feedback.models import AnalysisStatus, MetricSnapshot
from github_feedback.reporter import Reporter


@pytest.fixture
def sample_metrics() -> MetricSnapshot:
    """Provide a reusable metrics snapshot for reporter tests."""

    return MetricSnapshot(
        repo="example/repo",
        months=3,
        generated_at=datetime.utcnow(),
        status=AnalysisStatus.REPORTED,
        summary={"overall": "Consistent throughput across teams."},
        stats={
            "quality": {
                "mean_time_to_review": 12.3456,
                "long_identifier": 100,
            }
        },
        evidence={
            "quality": [
                "https://github.com/example/repo/pull/123/files#diff-"
                "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            ]
        },
    )


def test_generate_markdown_creates_expected_file(tmp_path, sample_metrics):
    """Markdown report should always be generated from provided metrics."""

    reporter = Reporter(output_dir=tmp_path)
    md_path = reporter.generate_markdown(sample_metrics)

    assert md_path.exists()
    contents = md_path.read_text(encoding="utf-8")
    assert "GitHub Feedback Report" in contents
