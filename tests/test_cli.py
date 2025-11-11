from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

import pytest
import typer

from github_feedback import cli
from github_feedback.config import AuthConfig, Config
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
    config = Config(auth=AuthConfig(pat="token"))
    monkeypatch.setattr(cli, "_load_config", lambda: config)
    return config


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

    def review_pull_request(self, repo: str, number: int) -> tuple[str, Path, Path, Path]:
        self.calls.append({"repo": repo, "number": number})
        base = Path(f"reviews/{repo.replace('/', '_')}/pr-{number}")
        return (
            f"Test PR #{number}",
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

    cli.brief(repo="example/repo")

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

    cli.brief(repo="example/repo")

    reporters = created.get("reporters", [])
    assert reporters, "Reporter should be instantiated"
    reporter = reporters[-1]
    assert reporter.markdown_calls, "Markdown report should be generated"
    # HTML is no longer an option in brief command
    assert not reporter.html_calls, "HTML report should not be generated"


def test_brief_uses_default_output_dir(monkeypatch: pytest.MonkeyPatch) -> None:
    _silent_console(monkeypatch)
    _stub_config(monkeypatch)
    created = _stub_dependencies(monkeypatch)

    cli.brief(repo="example/repo")

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

