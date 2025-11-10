from datetime import datetime, timezone

import pytest

pytest.importorskip("requests")

from github_feedback.collector import Collector
from github_feedback.config import AuthConfig, Config
from github_feedback.models import AnalysisFilters


def test_collector_filters_bots_and_counts_resources(monkeypatch):
    now = datetime.now(timezone.utc)
    config = Config(auth=AuthConfig(pat="dummy-token"))
    collector = Collector(config)

    def fake_request(path, params=None):  # type: ignore[override]
        params = params or {}
        page = params.get("page", 1)
        if path.endswith("/commits"):
            if page == 1:
                return [
                    {"author": {"type": "User"}},
                    {"author": {"type": "Bot"}},
                ]
            return []
        if path.endswith("/pulls"):
            if page == 1:
                return [
                    {
                        "number": 42,
                        "created_at": now.isoformat(),
                        "user": {"type": "User"},
                    },
                    {
                        "number": 43,
                        "created_at": now.isoformat(),
                        "user": {"type": "Bot"},
                    },
                ]
            return []
        if "reviews" in path:
            if page == 1:
                return [
                    {
                        "submitted_at": now.isoformat(),
                        "user": {"type": "User"},
                    },
                    {
                        "submitted_at": now.isoformat(),
                        "user": {"type": "Bot"},
                    },
                ]
            return []
        if path.endswith("/issues"):
            if page == 1:
                return [
                    {"user": {"type": "User"}},
                    {"pull_request": {}, "user": {"type": "User"}},
                ]
            return []
        raise AssertionError(f"Unhandled path {path}")

    monkeypatch.setattr(collector, "_request", fake_request)

    collection = collector.collect(
        repo="example/repo",
        months=1,
        filters=AnalysisFilters(),
    )

    assert collection.commits == 1
    assert collection.pull_requests == 1
    assert collection.reviews == 1
    assert collection.issues == 1


def test_collect_pull_request_details_paginates(monkeypatch):
    now = datetime.now(timezone.utc)
    config = Config(auth=AuthConfig(pat="dummy-token"))
    collector = Collector(config)

    def fake_request(path, params=None):  # type: ignore[override]
        params = params or {}
        page = params.get("page", 1)
        per_page = params.get("per_page", 100)
        if path.endswith("/reviews"):
            if page == 1:
                return [
                    {"submitted_at": now.isoformat(), "user": {"type": "User"}}
                    for _ in range(per_page)
                ]
            if page == 2:
                return [{"submitted_at": now.isoformat(), "user": {"type": "User"}}]
            return []
        if path.endswith("/comments"):
            if page == 1:
                return [{"body": f"comment-{idx}"} for idx in range(per_page)]
            if page == 2:
                return [{"body": "overflow"}]
            return []
        if path.endswith("/files"):
            if page == 1:
                return [
                    {
                        "filename": f"file{idx}.py",
                        "status": "modified",
                        "additions": idx,
                        "deletions": 0,
                        "changes": idx,
                    }
                    for idx in range(1, per_page + 1)
                ]
            if page == 2:
                return [
                    {
                        "filename": "file-last.py",
                        "status": "added",
                        "additions": 2,
                        "deletions": 0,
                        "changes": 2,
                        "patch": "@@",
                    }
                ]
            return []
        raise AssertionError(f"Unhandled path {path}")

    def fake_request_json(path, params=None):  # type: ignore[override]
        assert path.endswith("/pulls/7")
        return {
            "title": "Example PR",
            "body": "Improvements",
            "user": {"login": "octocat"},
            "html_url": "https://example.com/pr/7",
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
            "additions": 3,
            "deletions": 1,
            "changed_files": 2,
        }

    monkeypatch.setattr(collector, "_request", fake_request)
    monkeypatch.setattr(collector, "_request_json", fake_request_json)

    bundle = collector.collect_pull_request_details(repo="example/repo", number=7)

    assert len(bundle.review_bodies) == 0
    assert bundle.review_comments[0] == "comment-0"
    assert bundle.review_comments[-1] == "overflow"
    assert bundle.files[-1].patch == "@@"
