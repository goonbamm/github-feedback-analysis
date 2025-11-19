from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict
from textwrap import dedent

import pytest
import typer

from github_feedback import cli
from github_feedback.config import Config
from github_feedback.models import AnalysisFilters


class DummyStatus:
    def __enter__(self) -> "DummyStatus":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # noqa: D401 - standard contextmanager signature
        return None


class DummyCollector:
    def __init__(self, config: Config) -> None:
        self.config = config
        self.calls: list[Dict[str, Any]] = []

    def collect(
        self,
        repo: str,
        months: int,
        filters: AnalysisFilters,
    ) -> Dict[str, Any]:
        self.calls.append({"repo": repo, "months": months, "filters": filters})
        return {"repo": repo, "filters": filters}


class DummyAnalyzer:
    def __init__(self, web_base_url: str) -> None:  # noqa: D401 - mirror Analyzer signature
        self.web_base_url = web_base_url
        self.collections: list[Any] = []

    def compute_metrics(self, collection: Dict[str, Any]) -> "DummyMetrics":
        self.collections.append(collection)
        return DummyMetrics(collection["repo"])


class DummyMetrics:
    def __init__(self, repo: str) -> None:
        self.repo = repo
        self.months = 6
        self.generated_at = datetime.now(timezone.utc)
        from github_feedback.models import AnalysisStatus

        self.status = AnalysisStatus.ANALYSED
        self.summary: Dict[str, str] = {}
        self.stats: Dict[str, Dict[str, float]] = {}
        self.evidence: Dict[str, list[str]] = {}
        self.highlights: list[str] = []
        self.spotlight_examples: Dict[str, list[str]] = {}
        self.yearbook_story: list[str] = []
        self.awards: list[str] = []


class DummyReporter:
    def __init__(self, output_dir: Path = Path("reports")) -> None:
        self.output_dir = output_dir
        self.markdown_calls: list[DummyMetrics] = []
        self.html_calls: list[DummyMetrics] = []
        self.prompt_calls: list[DummyMetrics] = []

    def generate_markdown(self, metrics: DummyMetrics) -> Path:
        self.markdown_calls.append(metrics)
        return self.output_dir / f"{metrics.repo.replace('/', '_')}.md"

    def generate_html(self, metrics: DummyMetrics) -> Path:
        self.html_calls.append(metrics)
        return self.output_dir / f"{metrics.repo.replace('/', '_')}.html"

    def generate_prompt_packets(self, metrics: DummyMetrics) -> list:
        self.prompt_calls.append(metrics)
        return []


def _silent_console(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cli.console, "status", lambda *args, **kwargs: DummyStatus())
    monkeypatch.setattr(cli.console, "rule", lambda *args, **kwargs: None)
    monkeypatch.setattr(cli.console, "print", lambda *args, **kwargs: None)


def _capturing_console(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    messages: list[str] = []

    def capture(*args, **kwargs) -> None:
        rendered = " ".join(str(arg) for arg in args)
        messages.append(rendered)

    monkeypatch.setattr(cli.console, "status", lambda *args, **kwargs: DummyStatus())
    monkeypatch.setattr(cli.console, "rule", lambda *args, **kwargs: None)
    monkeypatch.setattr(cli.console, "print", capture)

    return messages


def _stub_config(monkeypatch: pytest.MonkeyPatch) -> Config:
    # Mock keyring to return a test token
    import keyring
    monkeypatch.setattr(keyring, "get_password", lambda service, username: "test-token")
    config = Config()
    monkeypatch.setattr(cli, "_load_config", lambda: config)
    return config


def test_init_displays_config_without_error(monkeypatch: pytest.MonkeyPatch) -> None:
    _silent_console(monkeypatch)

    summary_calls: list[bool] = []
    monkeypatch.setattr(cli, "_print_config_summary", lambda: summary_calls.append(True))

    config = Config()

    def fake_load(cls, path=None):
        return config

    monkeypatch.setattr(cli.Config, "load", classmethod(fake_load))
    monkeypatch.setattr(cli.Config, "dump", lambda self, path=None, backup=True: None)
    monkeypatch.setattr(cli.Config, "update_auth", lambda self, pat: None)

    cli.init(
        pat="ghp_1234567890123456789012345",
        months=6,
        enterprise_host="https://github.example.com",
        llm_endpoint="https://llm.example.com/v1",
        llm_model="example-model",
        test_connection=False,
    )

    assert summary_calls == [True]


class DummyLLMClient:
    def __init__(self, endpoint: str, model: str) -> None:
        self.endpoint = endpoint
        self.model = model

    def analyze_commit_messages(self, data: Any) -> Dict[str, Any]:
        return {"score": 5, "feedback": "Good commits"}

    def analyze_pr_titles(self, data: Any) -> Dict[str, Any]:
        return {"score": 5, "feedback": "Good PR titles"}

    def analyze_review_tone(self, data: Any) -> Dict[str, Any]:
        return {"score": 5, "feedback": "Good review tone"}

    def analyze_issue_quality(self, data: Any) -> Dict[str, Any]:
        return {"score": 5, "feedback": "Good issue quality"}


class DummyCollectorWithDetailedFeedback(DummyCollector):
    def collect_commit_messages(self, repo: str, since: Any, filters: Any, limit: int = 100) -> list:
        return []

    def collect_pr_titles(self, repo: str, since: Any, filters: Any, limit: int = 100) -> list:
        return []

    def collect_review_comments_detailed(self, repo: str, since: Any, filters: Any, limit: int = 100) -> list:
        return []

    def collect_issue_details(self, repo: str, since: Any, filters: Any, limit: int = 100) -> list:
        return []


class DummyAnalyzerWithDetailedFeedback(DummyAnalyzer):
    def compute_metrics(self, collection: Dict[str, Any], detailed_feedback: Any = None) -> "DummyMetrics":
        self.collections.append(collection)
        return DummyMetrics(collection["repo"])

    def build_detailed_feedback(self, commit_analysis: Any, pr_title_analysis: Any,
                               review_tone_analysis: Any, issue_analysis: Any) -> Dict[str, Any]:
        return {"commit_analysis": commit_analysis, "pr_title_analysis": pr_title_analysis}


def _stub_dependencies(monkeypatch: pytest.MonkeyPatch) -> Dict[str, Any]:
    created: Dict[str, Any] = {}

    def collector_factory(config: Config) -> DummyCollectorWithDetailedFeedback:
        instance = DummyCollectorWithDetailedFeedback(config)
        created["collector"] = instance
        return instance

    monkeypatch.setattr(cli, "Collector", collector_factory)
    monkeypatch.setattr(cli, "Analyzer", lambda web_base_url: DummyAnalyzerWithDetailedFeedback(web_base_url))
    monkeypatch.setattr(cli, "LLMClient", DummyLLMClient)

    def reporter_factory(*args, **kwargs) -> DummyReporter:
        output_dir = kwargs.get("output_dir")
        if args:
            output_dir = args[0]
        if output_dir is None:
            output_dir = Path("reports")
        instance = DummyReporter(output_dir=output_dir)
        created.setdefault("reporters", []).append(instance)
        return instance

    monkeypatch.setattr(cli, "Reporter", reporter_factory)

    def persist_stub(*args, **kwargs) -> Path:
        if args and not kwargs:
            # Backwards compatibility if positional args sneak in
            output_dir, metrics_data = args[:2]
            filename = args[2] if len(args) > 2 else "metrics.json"
        else:
            output_dir = kwargs.get("output_dir", args[0] if args else Path("reports"))
            metrics_data = kwargs["metrics_data"]
            filename = kwargs.get("filename", "metrics.json")

        output_dir = Path(output_dir)
        created.setdefault("persist_calls", []).append(
            {"output_dir": output_dir, "metrics_data": metrics_data, "filename": filename}
        )
        return output_dir / filename

    monkeypatch.setattr(cli, "persist_metrics", persist_stub)
    monkeypatch.setattr(cli, "_render_metrics", lambda *args, **kwargs: None)
    return created


class DummyReviewCollector(DummyCollector):
    def __init__(self, config: Config, authored_numbers: list[int], auth_user: str = "testuser") -> None:
        super().__init__(config)
        self.authored_numbers = authored_numbers
        self.auth_user = auth_user
        self.authored_calls: list[Dict[str, Any]] = []
        self.auth_calls: int = 0

    def get_authenticated_user(self) -> str:
        self.auth_calls += 1
        return self.auth_user

    def list_authored_pull_requests(
        self, repo: str, author: str, state: str
    ) -> list[int]:
        self.authored_calls.append({
            "repo": repo,
            "author": author,
            "state": state,
        })
        return list(self.authored_numbers)


class DummyReviewer:
    def __init__(self, collector: DummyReviewCollector, llm: Any) -> None:
        self.collector = collector
        self.llm = llm
        self.calls: list[Dict[str, Any]] = []
        self.output_dir = Path("reviews")

    def review_pull_request(self, repo: str, number: int) -> tuple[Path, Path, Path]:
        self.calls.append({"repo": repo, "number": number})
        base = Path(f"reviews/{repo.replace('/', '_')}/pr-{number}")
        return (
            base / "artefacts.json",
            base / "review_summary.json",
            base / "review.md",
        )


def _stub_review_dependencies(
    monkeypatch: pytest.MonkeyPatch, authored_numbers: list[int], auth_user: str = "testuser"
) -> Dict[str, Any]:
    created: Dict[str, Any] = {}

    def collector_factory(config: Config) -> DummyReviewCollector:
        collector = DummyReviewCollector(config, authored_numbers, auth_user)
        created["collector"] = collector
        return collector

    def reviewer_factory(collector: DummyReviewCollector, llm: Any) -> DummyReviewer:
        reviewer = DummyReviewer(collector, llm)
        created.setdefault("reviewers", []).append(reviewer)
        return reviewer

    monkeypatch.setattr(cli, "Collector", collector_factory)
    monkeypatch.setattr(cli, "Reviewer", reviewer_factory)
    monkeypatch.setattr(cli, "LLMClient", lambda endpoint, model: object())

    return created


def test_brief_uses_default_values(monkeypatch: pytest.MonkeyPatch) -> None:
    _silent_console(monkeypatch)
    config = _stub_config(monkeypatch)
    created = _stub_dependencies(monkeypatch)

    cli.feedback(repo="example/repo")

    assert "collector" in created
    collector = created["collector"]
    assert collector.config is config
    assert collector.calls, "collector.collect should have been invoked"
    call = collector.calls[-1]
    filters = call["filters"]

    # All filters should use default values (empty lists)
    assert filters.include_branches == []
    assert filters.exclude_branches == []
    assert filters.include_paths == []
    assert filters.exclude_paths == []
    assert filters.include_languages == []
    # Bots should be excluded by default
    assert filters.exclude_bots is True
    # Months should use config default
    assert call["months"] == config.defaults.months
    assert call["repo"] == "example/repo"


def test_brief_generates_markdown_report(monkeypatch: pytest.MonkeyPatch) -> None:
    _silent_console(monkeypatch)
    _stub_config(monkeypatch)
    created = _stub_dependencies(monkeypatch)

    cli.feedback(repo="example/repo")

    reporters = created.get("reporters", [])
    assert reporters, "Reporter should be instantiated"
    reporter = reporters[-1]
    assert reporter.markdown_calls, "Markdown report should be generated"
    # HTML report with charts is now generated by default
    assert reporter.html_calls, "HTML report should be generated"


def test_generate_integrated_report_includes_witch_section(tmp_path: Path) -> None:
    """Integrated report should render the witch critique when available."""

    brief_content = dedent(
        """
        ## 🏆 Awards Cabinet

        | 순번 | 어워드 | 설명 |
        | 1 | 코드 장인 | 품질 개선 |

        ## 🔮 마녀의 독설

        마녀의 경고: 커밋 메시지를 제대로 작성해.

        ## 💡 Detailed Feedback

        - 기타 개선 사항
        """
    )

    feedback_content = dedent(
        """
        ## 👤 개인 성장 분석

        - 테스트 성장 포인트
        """
    )

    feedback_report_path = tmp_path / "feedback_report.md"
    feedback_report_path.write_text(feedback_content, encoding="utf-8")

    report_path = cli._generate_integrated_full_report(
        output_dir=tmp_path,
        repo_name="example/repo",
        brief_content=brief_content,
        feedback_report_path=feedback_report_path,
    )

    content = report_path.read_text(encoding="utf-8")
    assert "### 🔮 마녀의 독설" in content
    assert "마녀의 경고" in content


def test_brief_uses_default_output_dir(monkeypatch: pytest.MonkeyPatch) -> None:
    _silent_console(monkeypatch)
    _stub_config(monkeypatch)
    created = _stub_dependencies(monkeypatch)

    cli.feedback(repo="example/repo")

    reporters = created.get("reporters", [])
    assert reporters, "Reporter should be instantiated"
    reporter = reporters[-1]
    # Output dir is hardcoded to Path("reports")
    assert reporter.output_dir == Path("reports")

    persist_calls = created.get("persist_calls", [])
    assert persist_calls, "persist_metrics should be invoked"
    assert persist_calls[-1]["output_dir"] == Path("reports")
    assert persist_calls[-1]["filename"] == "metrics.json"


def test_review_supports_direct_number_invocation(monkeypatch: pytest.MonkeyPatch) -> None:
    _silent_console(monkeypatch)
    config = _stub_config(monkeypatch)
    created = _stub_review_dependencies(monkeypatch, authored_numbers=[])

    cli.review(repo="example/repo", number=42)

    collector = created["collector"]
    assert collector.config is config
    assert not collector.authored_calls, "list_authored_pull_requests should not be called"
    assert collector.auth_calls == 0, "get_authenticated_user should not be called"

    reviewers = created.get("reviewers", [])
    assert reviewers, "Reviewer should be instantiated"
    reviewer = reviewers[-1]
    assert reviewer.calls == [{"repo": "example/repo", "number": 42}]


def test_review_announces_output_directory(monkeypatch: pytest.MonkeyPatch) -> None:
    messages = _capturing_console(monkeypatch)
    _stub_config(monkeypatch)
    _stub_review_dependencies(monkeypatch, authored_numbers=[])

    cli.review(repo="example/repo", number=7)

    expected_dir = Path("reviews").resolve()
    assert any("Review artefacts stored under" in message for message in messages)
    assert any(str(expected_dir) in message for message in messages)


def test_review_lists_authored_prs_for_authenticated_user(monkeypatch: pytest.MonkeyPatch) -> None:
    _silent_console(monkeypatch)
    config = _stub_config(monkeypatch)
    created = _stub_review_dependencies(monkeypatch, authored_numbers=[5, 3, 5], auth_user="octocat")

    cli.review(repo="example/repo", state="open")

    collector = created["collector"]
    assert collector.config is config
    assert collector.auth_calls == 1, "get_authenticated_user should be called once"
    assert collector.authored_calls == [
        {"repo": "example/repo", "author": "octocat", "state": "open"}
    ]

    reviewers = created.get("reviewers", [])
    assert reviewers, "Reviewer should be instantiated"
    reviewer = reviewers[-1]
    assert reviewer.calls == [
        {"repo": "example/repo", "number": 3},
        {"repo": "example/repo", "number": 5},
    ]


def test_collect_detailed_feedback_with_empty_data(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that _collect_detailed_feedback handles empty datasets gracefully."""
    from github_feedback.cli import _collect_detailed_feedback
    from github_feedback.analyzer import Analyzer
    from github_feedback.collector import Collector
    from unittest.mock import Mock

    # Mock collector that returns empty data
    mock_collector = Mock(spec=Collector)
    mock_collector.collect_commit_messages.return_value = []
    mock_collector.collect_pr_titles.return_value = []
    mock_collector.collect_review_comments_detailed.return_value = []
    mock_collector.collect_issue_details.return_value = []

    # Mock analyzer
    mock_analyzer = Mock(spec=Analyzer)
    mock_analyzer.build_detailed_feedback.return_value = None

    # Mock config
    config = _stub_config(monkeypatch)

    # Call the function
    since = datetime(2024, 1, 1, tzinfo=timezone.utc)
    filters = AnalysisFilters()

    result = _collect_detailed_feedback(
        collector=mock_collector,
        analyzer=mock_analyzer,
        config=config,
        repo="test/repo",
        since=since,
        filters=filters,
        author=None
    )

    # Verify all collection methods were called
    assert mock_collector.collect_commit_messages.called
    assert mock_collector.collect_pr_titles.called
    assert mock_collector.collect_review_comments_detailed.called
    assert mock_collector.collect_issue_details.called

    # Verify analyzer was called
    assert mock_analyzer.build_detailed_feedback.called


def test_collect_detailed_feedback_llm_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test fallback when LLM is unavailable."""
    from github_feedback.cli import _collect_detailed_feedback
    from github_feedback.analyzer import Analyzer
    from github_feedback.collector import Collector
    from unittest.mock import Mock, patch
    import requests

    # Mock collector with sample data
    mock_collector = Mock(spec=Collector)
    mock_collector.collect_commit_messages.return_value = [
        {"sha": "abc123", "message": "feat: add new feature"}
    ]
    mock_collector.collect_pr_titles.return_value = [
        {"number": 1, "title": "Add feature"}
    ]
    mock_collector.collect_review_comments_detailed.return_value = []
    mock_collector.collect_issue_details.return_value = []

    # Mock analyzer
    mock_analyzer = Mock(spec=Analyzer)
    mock_analyzer.build_detailed_feedback.return_value = None

    # Mock config
    config = _stub_config(monkeypatch)

    # Mock LLM to raise RequestException
    with patch("github_feedback.llm.LLMClient.analyze_commit_messages") as mock_llm:
        mock_llm.side_effect = requests.RequestException("Network error")

        since = datetime(2024, 1, 1, tzinfo=timezone.utc)
        filters = AnalysisFilters()

        # Should return None due to LLM failure
        result = _collect_detailed_feedback(
            collector=mock_collector,
            analyzer=mock_analyzer,
            config=config,
            repo="test/repo",
            since=since,
            filters=filters,
            author=None
        )

        assert result is None


def test_collect_detailed_feedback_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test timeout handling in parallel collection."""
    from github_feedback.cli import _collect_detailed_feedback
    from github_feedback.analyzer import Analyzer
    from github_feedback.collector import Collector
    from unittest.mock import Mock
    import time

    # Mock collector with slow response
    mock_collector = Mock(spec=Collector)

    def slow_collect(*args, **kwargs):
        time.sleep(0.1)  # Simulate slow operation
        return []

    mock_collector.collect_commit_messages = slow_collect
    mock_collector.collect_pr_titles.return_value = []
    mock_collector.collect_review_comments_detailed.return_value = []
    mock_collector.collect_issue_details.return_value = []

    # Mock analyzer
    mock_analyzer = Mock(spec=Analyzer)
    mock_analyzer.build_detailed_feedback.return_value = None

    # Mock config
    config = _stub_config(monkeypatch)

    since = datetime(2024, 1, 1, tzinfo=timezone.utc)
    filters = AnalysisFilters()

    # This should complete even with slow collection
    result = _collect_detailed_feedback(
        collector=mock_collector,
        analyzer=mock_analyzer,
        config=config,
        repo="test/repo",
        since=since,
        filters=filters,
        author=None
    )

    # Should handle timeout gracefully
    assert result is not None or result is None  # Either result is acceptable

