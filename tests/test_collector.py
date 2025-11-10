from datetime import datetime, timezone
from typing import Any, Dict, List

import pytest

pytest.importorskip("requests")

import requests

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
                    {"sha": "sha-1", "author": {"type": "User"}},
                    {"sha": "sha-2", "author": {"type": "Bot"}},
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


@pytest.mark.parametrize(
    "include_languages",
    [["Python"], ["py"]],
)
def test_collector_applies_branch_path_and_language_filters(
    monkeypatch: pytest.MonkeyPatch, include_languages: List[str]
):
    now = datetime.now(timezone.utc)
    config = Config(auth=AuthConfig(pat="dummy-token"))
    collector = Collector(config)

    commit_pages = {
        ("main", "src/app.py"): [
            {"sha": "c-main", "author": {"type": "User"}},
        ],
        ("main", "docs/readme.md"): [
            {"sha": "c-main-docs", "author": {"type": "User"}},
        ],
        ("feature", "src/app.py"): [
            {"sha": "c-feature", "author": {"type": "User"}},
            {"sha": "c-main", "author": {"type": "User"}},
        ],
        ("feature", "docs/readme.md"): [],
    }

    commit_details = {
        "c-main": {"files": [{"filename": "src/app.py"}]},
        "c-main-docs": {
            "files": [{"filename": "docs/old/guide.md"}],
        },
        "c-feature": {"files": [{"filename": "src/app.py"}]},
    }

    pr_pages = [
        {
            "number": 1,
            "created_at": now.isoformat(),
            "user": {"type": "User"},
            "base": {"ref": "main"},
            "head": {"ref": "feature"},
        },
        {
            "number": 2,
            "created_at": now.isoformat(),
            "user": {"type": "User"},
            "base": {"ref": "deprecated"},
            "head": {"ref": "feature"},
        },
        {
            "number": 3,
            "created_at": now.isoformat(),
            "user": {"type": "User"},
            "base": {"ref": "main"},
            "head": {"ref": "docs-update"},
        },
    ]

    pr_files = {
        1: [
            {"filename": "src/app.py"},
            {"filename": "docs/guide.md"},
        ],
        2: [
            {"filename": "src/legacy.py"},
        ],
        3: [
            {"filename": "docs/old/manual.md"},
        ],
    }

    review_pages = {
        1: [
            {
                "submitted_at": now.isoformat(),
                "user": {"type": "User"},
            }
        ],
        2: [
            {
                "submitted_at": now.isoformat(),
                "user": {"type": "User"},
            }
        ],
        3: [
            {
                "submitted_at": now.isoformat(),
                "user": {"type": "User"},
            }
        ],
    }

    issues_page = [
        {"user": {"type": "User"}, "files": ["src/app.py"]},
        {"user": {"type": "User"}, "files": ["docs/old/guide.md"]},
        {"user": {"type": "User"}, "files": ["tests/test_app.py"]},
        {"user": {"type": "User"}, "pull_request": {}},
    ]

    def fake_request(path, params=None):  # type: ignore[override]
        params = params or {}
        page = params.get("page", 1)
        if path.endswith("/commits") and "pulls" not in path:
            if page > 1:
                return []
            sha = params.get("sha")
            path_filter = params.get("path")
            if sha is None:
                return []
            if path_filter == "src/":
                key = (sha, "src/app.py")
            elif path_filter == "docs/":
                key = (sha, "docs/readme.md")
            else:
                key = (sha, path_filter)
            return commit_pages.get(key, [])
        if path.endswith("/pulls"):
            if page > 1:
                return []
            return pr_pages
        if path.endswith("/reviews"):
            number = int(path.rstrip("/").split("/")[-2])
            if page > 1:
                return []
            return review_pages[number]
        if path.endswith("/files"):
            number = int(path.rstrip("/").split("/")[-2])
            if page > 1:
                return []
            return pr_files[number]
        if path.endswith("/issues"):
            if page > 1:
                return []
            return issues_page
        raise AssertionError(f"Unhandled path {path}")

    def fake_request_json(path, params=None):  # type: ignore[override]
        if "/commits/" in path:
            sha = path.rsplit("/", 1)[-1]
            return commit_details[sha]
        raise AssertionError(f"Unhandled json path {path}")

    monkeypatch.setattr(collector, "_request", fake_request)
    monkeypatch.setattr(collector, "_request_json", fake_request_json)

    filters = AnalysisFilters(
        include_branches=["main", "feature"],
        exclude_branches=["deprecated"],
        include_paths=["src/", "docs/"],
        exclude_paths=["docs/old"],
        include_languages=include_languages,
    )

    collection = collector.collect(
        repo="example/repo",
        months=1,
        filters=filters,
    )

    assert collection.commits == 2
    assert collection.pull_requests == 1
    assert collection.reviews == 1
    assert collection.issues == 1


def test_list_assigned_pull_requests_filters_prs(monkeypatch):
    collector = Collector(Config(auth=AuthConfig(pat="token")))

    issues_payload = [
        {"number": 1, "pull_request": {}},
        {"number": 2},
        {"number": 3, "pull_request": {}},
        {"number": 1, "pull_request": {}},
    ]

    def fake_request_all(self, path, params=None):  # type: ignore[override]
        assert path == "repos/example/repo/issues"
        assert params == {"assignee": "octocat", "state": "closed", "per_page": 100}
        return issues_payload

    monkeypatch.setattr(Collector, "_request_all", fake_request_all)

    numbers = collector.list_assigned_pull_requests(
        repo="example/repo",
        assignee="octocat",
        state="CLOSED",
    )

    assert numbers == [1, 3]


def test_list_assigned_pull_requests_validates_state():
    collector = Collector(Config(auth=AuthConfig(pat="token")))

    with pytest.raises(ValueError):
        collector.list_assigned_pull_requests("example/repo", "octocat", state="invalid")
