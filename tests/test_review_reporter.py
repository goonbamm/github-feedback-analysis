from __future__ import annotations

import json
from datetime import datetime

import pytest

from github_feedback.reporters.review_reporter import ReviewReporter


def _write_review(tmp_path, repo: str, number: int, *, overview: str = "") -> None:
    root = tmp_path / "reviews" / repo.replace("/", "__") / f"pr-{number}"
    root.mkdir(parents=True, exist_ok=True)

    artefact_payload = {
        "repo": repo,
        "number": number,
        "title": f"Feature {number}",
        "author": "alice",
        "html_url": f"https://example.com/{repo}/pull/{number}",
        "created_at": datetime(2024, 1, number).isoformat(),
    }

    summary_payload = {
        "overview": overview or f"PR #{number} adds helpful changes.",
        "strengths": [
            {"message": "잘 구조화된 변경", "example": "폴더 구조를 단순화"},
        ],
        "improvements": [
            {"message": "테스트 보강 필요", "example": "엣지 케이스 테스트 없음"},
        ],
    }

    (root / "artefacts.json").write_text(
        json.dumps(artefact_payload, ensure_ascii=False),
        encoding="utf-8",
    )
    (root / "review_summary.json").write_text(
        json.dumps(summary_payload, ensure_ascii=False),
        encoding="utf-8",
    )


def test_review_reporter_creates_fallback_report(tmp_path) -> None:
    _write_review(tmp_path, "octocat/hello", 1)

    reporter = ReviewReporter(output_dir=tmp_path / "reviews", llm=None)
    report_path = reporter.create_integrated_report("octocat/hello")

    content = report_path.read_text(encoding="utf-8")
    assert "통합 코드 리뷰 보고서" in content
    assert "## 장점" in content
    assert "PR #1" in content


def test_review_reporter_uses_llm_when_available(tmp_path) -> None:
    _write_review(tmp_path, "octocat/hello", 2, overview="API 품질 개선")

    class DummyLLM:
        def __init__(self) -> None:
            self.messages = None

        def complete(self, messages, *, temperature: float = 0.3):
            self.messages = messages
            return "# 통합 보고서\n\n## 장점\n- 예시"

    dummy_llm = DummyLLM()
    reporter = ReviewReporter(output_dir=tmp_path / "reviews", llm=dummy_llm)
    report_path = reporter.create_integrated_report("octocat/hello")

    assert dummy_llm.messages is not None
    assert report_path.read_text(encoding="utf-8").startswith("# 통합 보고서")


def test_review_reporter_errors_when_missing_reviews(tmp_path) -> None:
    reporter = ReviewReporter(output_dir=tmp_path / "reviews")
    with pytest.raises(ValueError):
        reporter.create_integrated_report("octocat/hello")


def test_review_reporter_handles_multiple_prs(tmp_path) -> None:
    """Test reporter handles multiple PRs correctly."""
    _write_review(tmp_path, "octocat/hello", 1)
    _write_review(tmp_path, "octocat/hello", 2)
    _write_review(tmp_path, "octocat/hello", 3)

    reporter = ReviewReporter(output_dir=tmp_path / "reviews", llm=None)
    report_path = reporter.create_integrated_report("octocat/hello")

    content = report_path.read_text(encoding="utf-8")
    assert "PR #1" in content
    assert "PR #2" in content
    assert "PR #3" in content


def test_review_reporter_handles_special_characters_in_repo_name(tmp_path) -> None:
    """Test reporter handles repository names with special characters."""
    _write_review(tmp_path, "org/repo-name", 1)

    reporter = ReviewReporter(output_dir=tmp_path / "reviews", llm=None)
    report_path = reporter.create_integrated_report("org/repo-name")

    assert report_path.exists()
    content = report_path.read_text(encoding="utf-8")
    assert "통합 코드 리뷰 보고서" in content


def test_review_reporter_output_path(tmp_path) -> None:
    """Test reporter creates correct output path."""
    _write_review(tmp_path, "octocat/hello", 1)

    reporter = ReviewReporter(output_dir=tmp_path / "reviews", llm=None)
    report_path = reporter.create_integrated_report("octocat/hello")

    expected_path = tmp_path / "reviews" / "octocat__hello" / "integrated_review_report.md"
    assert report_path == expected_path
    assert report_path.exists()


def test_review_reporter_preserves_korean_encoding(tmp_path) -> None:
    """Test reporter preserves Korean text encoding."""
    _write_review(tmp_path, "octocat/hello", 1, overview="한글 테스트 내용")

    reporter = ReviewReporter(output_dir=tmp_path / "reviews", llm=None)
    report_path = reporter.create_integrated_report("octocat/hello")

    content = report_path.read_text(encoding="utf-8")
    assert "한글 테스트 내용" in content
    assert "잘 구조화된 변경" in content


def test_review_reporter_fallback_when_llm_fails(tmp_path) -> None:
    """Test reporter falls back to template when LLM fails."""
    _write_review(tmp_path, "octocat/hello", 1)

    class FailingLLM:
        def complete(self, messages, *, temperature: float = 0.3):
            raise Exception("LLM API failed")

    reporter = ReviewReporter(output_dir=tmp_path / "reviews", llm=FailingLLM())
    report_path = reporter.create_integrated_report("octocat/hello")

    # Should fall back to template-based report
    content = report_path.read_text(encoding="utf-8")
    assert "통합 코드 리뷰 보고서" in content
    assert "## 장점" in content


def test_review_reporter_empty_strengths_and_improvements(tmp_path) -> None:
    """Test reporter handles PRs with empty strengths/improvements."""
    root = tmp_path / "reviews" / "octocat__hello" / "pr-1"
    root.mkdir(parents=True, exist_ok=True)

    artefact_payload = {
        "repo": "octocat/hello",
        "number": 1,
        "title": "Test PR",
        "author": "testuser",
        "html_url": "https://example.com/pr/1",
        "created_at": datetime(2024, 1, 1).isoformat(),
    }

    summary_payload = {
        "overview": "Test overview",
        "strengths": [],
        "improvements": [],
    }

    (root / "artefacts.json").write_text(
        json.dumps(artefact_payload, ensure_ascii=False),
        encoding="utf-8",
    )
    (root / "review_summary.json").write_text(
        json.dumps(summary_payload, ensure_ascii=False),
        encoding="utf-8",
    )

    reporter = ReviewReporter(output_dir=tmp_path / "reviews", llm=None)
    report_path = reporter.create_integrated_report("octocat/hello")

    content = report_path.read_text(encoding="utf-8")
    assert "통합 코드 리뷰 보고서" in content
