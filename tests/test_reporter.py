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
    assert "Long Identifier" in contents and "100" in contents


def test_generate_markdown_includes_growth_sections(tmp_path):
    """Growth highlights and examples should render when provided."""

    metrics = MetricSnapshot(
        repo="example/repo",
        months=12,
        generated_at=datetime.utcnow(),
        status=AnalysisStatus.ANALYSED,
        summary={"overall": "Busy year"},
        stats={},
        evidence={},
        highlights=["올해에 120회의 커밋으로 코드 품질을 끌어올렸습니다."],
        spotlight_examples={
            "pull_requests": [
                "PR #42 · Add analytics API — dev1 (2024-02-01, 2024-02-03 병합, 변경 200줄) · https://example.com"
            ]
        },
        yearbook_story=["올해는 핵심 기능을 대거 정비하며 팀의 속도를 끌어올렸습니다."],
        awards=["🏆 코드 대장장이 상 — 100회 이상의 커밋"]
    )

    reporter = Reporter(output_dir=tmp_path)
    md_path = reporter.generate_markdown(metrics)

    contents = md_path.read_text(encoding="utf-8")
    assert "Growth Highlights" in contents
    assert "올해에 120회의 커밋" in contents
    assert "Spotlight Examples" in contents
    assert "PR #42" in contents
    assert "Year in Review" in contents
    assert "핵심 기능을 대거 정비" in contents
    assert "Awards Cabinet" in contents
    assert "코드 대장장이 상" in contents


def test_generate_markdown_content_returns_string(tmp_path, sample_metrics):
    """Test that generate_markdown_content returns markdown content without writing to file."""

    reporter = Reporter(output_dir=tmp_path)
    content = reporter.generate_markdown_content(sample_metrics)

    # Should return a non-empty string
    assert isinstance(content, str)
    assert len(content) > 0

    # Should contain expected sections
    assert "# 🚀 GitHub Feedback Report" in content
    assert "example/repo" in content
    assert "## 📊 Executive Summary" in content

    # Should NOT create a file
    report_path = tmp_path / "report.md"
    assert not report_path.exists()


def test_generate_prompt_packets_builds_multi_angle_requests(
    tmp_path, sample_metrics
):
    """Prompt packet generation should provide ready-to-send instructions.

    NOTE: This test is kept for backward compatibility with the generate_prompt_packets method,
    but the CLI no longer uses this functionality (prompts folder is no longer generated).
    """

    reporter = Reporter(output_dir=tmp_path)
    packets = reporter.generate_prompt_packets(sample_metrics)

    assert len(packets) == 5

    titles = [request.title for request, _ in packets]
    assert any("성과" in title or "핵심" in title for title in titles)
    assert any("목표" in title for title in titles)

    for request, prompt_path in packets:
        assert prompt_path.exists()
        contents = prompt_path.read_text(encoding="utf-8")
        assert request.instructions in contents
        assert "## Prompt" in contents
        assert "Repository: example/repo" in contents
        assert "Summary:" in request.prompt
