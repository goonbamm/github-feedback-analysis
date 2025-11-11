from __future__ import annotations

import json
from datetime import datetime

import pytest

from github_feedback.review_reporter import ReviewReporter


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
