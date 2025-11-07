"""Tests for the PDF and markdown reporter outputs."""

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


def test_generate_pdf_handles_long_tokens(tmp_path, sample_metrics):
    """Ensure PDF generation succeeds even with very long evidence URLs."""

    reporter = Reporter(output_dir=tmp_path)
    pdf_path = reporter.generate_pdf(sample_metrics)

    assert pdf_path.exists()
    assert pdf_path.stat().st_size > 0


def test_generate_markdown_creates_expected_file(tmp_path, sample_metrics):
    """Markdown report should always be generated alongside PDF support."""

    reporter = Reporter(output_dir=tmp_path)
    md_path = reporter.generate_markdown(sample_metrics)

    assert md_path.exists()
    contents = md_path.read_text(encoding="utf-8")
    assert "GitHub Feedback Report" in contents


def test_generate_pdf_renders_hangul_text(tmp_path):
    """Verify Hangul content is emitted without raising rendering errors."""

    metrics = MetricSnapshot(
        repo="예시/저장소",
        months=6,
        generated_at=datetime.utcnow(),
        status=AnalysisStatus.REPORTED,
        summary={
            "현황": "한글 요약이 정확하게 표시되는지 검증합니다.",
            "세부": "리뷰 사이클이 안정적이며 협업 만족도가 높습니다.",
        },
        stats={
            "품질": {
                "평균_리뷰_시간": 12.5,
                "주요_메트릭": "지속적인 품질 개선",
            }
        },
        evidence={
            "품질": [
                "https://github.com/예시/저장소/pull/42",
                "https://서비스.한국/피드백/상세",
                "가나다라마바사아자차카타파하" * 3,
            ]
        },
    )

    reporter = Reporter(output_dir=tmp_path)
    pdf_path = reporter.generate_pdf(metrics)

    assert pdf_path.exists()
    assert pdf_path.stat().st_size > 0
