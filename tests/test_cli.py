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


def _stub_dependencies(monkeypatch: pytest.MonkeyPatch) -> Dict[str, Any]:
    created: Dict[str, Any] = {}

    def collector_factory(config: Config) -> DummyCollector:
        instance = DummyCollector(config)
        created["collector"] = instance
        return instance

    monkeypatch.setattr(cli, "Collector", collector_factory)
    monkeypatch.setattr(cli, "Analyzer", lambda web_base_url: DummyAnalyzer(web_base_url))

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
    def __init__(self, config: Config, assigned_numbers: list[int]) -> None:
        super().__init__(config)
        self.assigned_numbers = assigned_numbers
        self.assigned_calls: list[Dict[str, Any]] = []

    def list_assigned_pull_requests(
        self, repo: str, assignee: str, state: str
    ) -> list[int]:
        self.assigned_calls.append({
            "repo": repo,
            "assignee": assignee,
            "state": state,
        })
        return list(self.assigned_numbers)


class DummyReviewer:
    def __init__(self, collector: DummyReviewCollector, llm: Any) -> None:
        self.collector = collector
        self.llm = llm
        self.calls: list[Dict[str, Any]] = []

    def review_pull_request(self, repo: str, number: int) -> tuple[Path, Path, Path]:
        self.calls.append({"repo": repo, "number": number})
        base = Path(f"reviews/{repo.replace('/', '_')}/pr-{number}")
        return (
            base / "artefacts.json",
            base / "review_summary.json",
            base / "review.md",
        )


def _stub_review_dependencies(
    monkeypatch: pytest.MonkeyPatch, assigned_numbers: list[int]
) -> Dict[str, Any]:
    created: Dict[str, Any] = {}

    def collector_factory(config: Config) -> DummyReviewCollector:
        collector = DummyReviewCollector(config, assigned_numbers)
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


def test_analyze_supports_multiple_filter_options(monkeypatch: pytest.MonkeyPatch) -> None:
    _silent_console(monkeypatch)
    config = _stub_config(monkeypatch)
    created = _stub_dependencies(monkeypatch)

    cli.analyze(
        repo="example/repo",
        months=6,
        include_branch=["main", "release"],
        exclude_branch=["legacy"],
        include_path=["src/", "docs/"],
        exclude_path=["tests/"],
        include_language=["py", "md"],
        include_bots=True,
    )

    assert "collector" in created
    collector = created["collector"]
    assert collector.config is config
    assert collector.calls, "collector.collect should have been invoked"
    call = collector.calls[-1]
    filters = call["filters"]

    assert filters.include_branches == ["main", "release"]
    assert filters.exclude_branches == ["legacy"]
    assert filters.include_paths == ["src/", "docs/"]
    assert filters.exclude_paths == ["tests/"]
    assert filters.include_languages == ["py", "md"]
    assert filters.exclude_bots is False
    assert call["months"] == 6
    assert call["repo"] == "example/repo"

    # Ensure analyzer received the collection and config defaults were respected
    assert config.defaults.months == 12


def test_analyze_generates_html_when_requested(monkeypatch: pytest.MonkeyPatch) -> None:
    _silent_console(monkeypatch)
    _stub_config(monkeypatch)
    created = _stub_dependencies(monkeypatch)

    cli.analyze(
        repo="example/repo",
        months=3,
        include_branch=None,
        exclude_branch=None,
        include_path=None,
        exclude_path=None,
        include_language=None,
        include_bots=False,
        html=True,
    )

    reporters = created.get("reporters", [])
    assert reporters, "Reporter should be instantiated"
    reporter = reporters[-1]
    assert reporter.markdown_calls, "Markdown report should be generated"
    assert reporter.html_calls, "HTML report should be generated when --html is provided"


def test_analyze_uses_custom_output_dir(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _silent_console(monkeypatch)
    _stub_config(monkeypatch)
    created = _stub_dependencies(monkeypatch)

    cli.analyze(
        repo="example/repo",
        months=3,
        include_branch=None,
        exclude_branch=None,
        include_path=None,
        exclude_path=None,
        include_language=None,
        include_bots=False,
        html=False,
        output_dir=tmp_path,
    )

    reporters = created.get("reporters", [])
    assert reporters, "Reporter should be instantiated"
    reporter = reporters[-1]
    assert reporter.output_dir == tmp_path

    persist_calls = created.get("persist_calls", [])
    assert persist_calls, "persist_metrics should be invoked"
    assert persist_calls[-1]["output_dir"] == tmp_path
    assert persist_calls[-1]["filename"] == "metrics.json"


def test_report_generates_html_when_requested(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _silent_console(monkeypatch)
    _stub_config(monkeypatch)
    created = _stub_dependencies(monkeypatch)

    metrics_payload = {
        "repo": "example/repo",
        "months": 6,
        "generated_at": "2024-01-01T00:00:00",
        "status": "analysed",
        "summary": {},
        "stats": {},
        "evidence": {},
        "highlights": [],
        "spotlight_examples": {},
        "yearbook_story": [],
        "awards": [],
    }

    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    metrics_file = reports_dir / "metrics.json"
    metrics_file.write_text(json.dumps(metrics_payload), encoding="utf-8")

    monkeypatch.chdir(tmp_path)

    cli.report(html=True)

    reporters = created.get("reporters", [])
    assert reporters, "Reporter should be instantiated"
    reporter = reporters[-1]
    assert reporter.markdown_calls, "Markdown report should be regenerated"
    assert reporter.html_calls, "HTML report should be generated when --html is provided"


def test_report_respects_custom_output_dir(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _silent_console(monkeypatch)
    _stub_config(monkeypatch)
    created = _stub_dependencies(monkeypatch)

    metrics_payload = {
        "repo": "example/repo",
        "months": 6,
        "generated_at": "2024-01-01T00:00:00",
        "status": "analysed",
        "summary": {},
        "stats": {},
        "evidence": {},
        "highlights": [],
        "spotlight_examples": {},
        "yearbook_story": [],
        "awards": [],
    }

    custom_dir = tmp_path / "artifacts"
    custom_dir.mkdir()
    metrics_file = custom_dir / "metrics.json"
    metrics_file.write_text(json.dumps(metrics_payload), encoding="utf-8")

    cli.report(html=False, output_dir=custom_dir)

    reporters = created.get("reporters", [])
    assert reporters, "Reporter should be instantiated"
    reporter = reporters[-1]
    assert reporter.output_dir == custom_dir


def test_report_exits_on_corrupted_metrics_cache(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    messages = _capturing_console(monkeypatch)

    metrics_file = tmp_path / "metrics.json"
    metrics_file.write_text("{ invalid json", encoding="utf-8")

    with pytest.raises(typer.Exit) as excinfo:
        cli.report(output_dir=tmp_path)

    assert excinfo.value.exit_code == 1
    assert any("corrupted" in message.lower() for message in messages)
    assert any(str(metrics_file) in message for message in messages)


def test_review_supports_direct_number_invocation(monkeypatch: pytest.MonkeyPatch) -> None:
    _silent_console(monkeypatch)
    config = _stub_config(monkeypatch)
    created = _stub_review_dependencies(monkeypatch, assigned_numbers=[])

    cli.review(repo="example/repo", number=42)

    collector = created["collector"]
    assert collector.config is config
    assert not collector.assigned_calls, "list_assigned_pull_requests should not be called"

    reviewers = created.get("reviewers", [])
    assert reviewers, "Reviewer should be instantiated"
    reviewer = reviewers[-1]
    assert reviewer.calls == [{"repo": "example/repo", "number": 42}]


def test_review_lists_assignments_for_assignee(monkeypatch: pytest.MonkeyPatch) -> None:
    _silent_console(monkeypatch)
    config = _stub_config(monkeypatch)
    created = _stub_review_dependencies(monkeypatch, assigned_numbers=[5, 3, 5])

    cli.review(repo="example/repo", assignee="octocat", state="open")

    collector = created["collector"]
    assert collector.config is config
    assert collector.assigned_calls == [
        {"repo": "example/repo", "assignee": "octocat", "state": "open"}
    ]

    reviewers = created.get("reviewers", [])
    assert reviewers, "Reviewer should be instantiated"
    reviewer = reviewers[-1]
    assert reviewer.calls == [
        {"repo": "example/repo", "number": 3},
        {"repo": "example/repo", "number": 5},
    ]

