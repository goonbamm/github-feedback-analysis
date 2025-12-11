"""Integration tests for refactored collector architecture."""

import pytest

from github_feedback.api.client import GitHubApiClient
from github_feedback.collectors.analytics import AnalyticsCollector
from github_feedback.collectors.base import BaseCollector
from github_feedback.collectors.collector import Collector
from github_feedback.collectors.commits import CommitCollector
from github_feedback.core.config import Config
from github_feedback.core.exceptions import ConfigurationError
from github_feedback.filters import FilterHelper, LANGUAGE_EXTENSION_MAP
from github_feedback.collectors.issues import IssueCollector
from github_feedback.collectors.prs import PullRequestCollector
from github_feedback.collectors.reviews import ReviewCollector


def test_collector_facade_initialization(monkeypatch):
    """Test that Collector facade properly initializes all sub-collectors."""
    import keyring

    monkeypatch.setattr(
        keyring, "get_password", lambda service, username: "dummy-token"
    )

    config = Config()
    collector = Collector(config)

    # Verify all sub-collectors are initialized
    assert isinstance(collector.api_client, GitHubApiClient)
    assert isinstance(collector.commit_collector, CommitCollector)
    assert isinstance(collector.pr_collector, PullRequestCollector)
    assert isinstance(collector.review_collector, ReviewCollector)
    assert isinstance(collector.issue_collector, IssueCollector)
    assert isinstance(collector.analytics_collector, AnalyticsCollector)

    # Verify all sub-collectors share the same API client
    assert collector.commit_collector.api_client is collector.api_client
    assert collector.pr_collector.api_client is collector.api_client
    assert collector.review_collector.api_client is collector.api_client
    assert collector.issue_collector.api_client is collector.api_client
    assert collector.analytics_collector.api_client is collector.api_client


def test_api_client_requires_pat(monkeypatch):
    """Test that API client raises error when PAT is missing."""
    import keyring

    # Mock keyring to return None (no PAT configured)
    monkeypatch.setattr(keyring, "get_password", lambda service, username: None)

    config = Config()

    with pytest.raises(ConfigurationError, match="Authentication PAT is not configured"):
        GitHubApiClient(config)


def test_filter_helper_language_mapping():
    """Test that FilterHelper correctly maps file extensions to languages."""
    assert FilterHelper.filename_to_language("app.py") == "Python"
    assert FilterHelper.filename_to_language("script.js") == "JavaScript"
    assert FilterHelper.filename_to_language("component.tsx") == "TypeScript"
    assert FilterHelper.filename_to_language("noextension") is None
    assert FilterHelper.filename_to_language("unknown.xyz") is None


def test_filter_helper_language_tokens():
    """Test that FilterHelper extracts correct language tokens."""
    tokens = FilterHelper.filename_language_tokens("app.py")
    assert "py" in tokens
    assert "python" in tokens

    tokens = FilterHelper.filename_language_tokens("component.tsx")
    assert "tsx" in tokens
    assert "typescript" in tokens


def test_filter_helper_path_matching():
    """Test that FilterHelper correctly matches paths."""
    assert FilterHelper.path_matches("src/app.py", "src/")
    assert FilterHelper.path_matches("src/lib/utils.py", "src/")
    assert not FilterHelper.path_matches("tests/test.py", "src/")
    assert FilterHelper.path_matches("any/path.py", "")  # Empty prefix matches all


def test_filter_helper_extract_issue_files():
    """Test that FilterHelper extracts files from issue metadata."""
    issue = {
        "files": ["src/app.py", "src/lib.py"],
        "labels": [
            {"name": "path:docs/"},
            {"name": "file:readme.md"},
            {"name": "bug"},  # Non-file label
        ],
    }
    files = FilterHelper.extract_issue_files(issue)
    assert "src/app.py" in files
    assert "src/lib.py" in files
    assert "docs/" in files
    assert "readme.md" in files
    assert len(files) == 4


def test_base_collector_timestamp_parsing():
    """Test that BaseCollector correctly parses timestamps."""
    from datetime import datetime, timezone

    # ISO format with Z
    dt = BaseCollector.parse_timestamp("2024-01-15T10:30:00Z")
    assert dt.year == 2024
    assert dt.month == 1
    assert dt.day == 15
    assert dt.hour == 10
    assert dt.minute == 30

    # ISO format with timezone
    dt = BaseCollector.parse_timestamp("2024-01-15T10:30:00+00:00")
    assert dt.year == 2024
    assert dt.month == 1
    assert dt.day == 15


def test_language_extension_map_completeness():
    """Test that LANGUAGE_EXTENSION_MAP contains expected languages."""
    assert "py" in LANGUAGE_EXTENSION_MAP
    assert "js" in LANGUAGE_EXTENSION_MAP
    assert "ts" in LANGUAGE_EXTENSION_MAP
    assert "go" in LANGUAGE_EXTENSION_MAP
    assert "rs" in LANGUAGE_EXTENSION_MAP
    assert "java" in LANGUAGE_EXTENSION_MAP

    # Verify mappings
    assert LANGUAGE_EXTENSION_MAP["py"] == "Python"
    assert LANGUAGE_EXTENSION_MAP["js"] == "JavaScript"
    assert LANGUAGE_EXTENSION_MAP["ts"] == "TypeScript"
    assert LANGUAGE_EXTENSION_MAP["go"] == "Go"
    assert LANGUAGE_EXTENSION_MAP["rs"] == "Rust"


def test_collector_facade_delegates_to_specialized_collectors(monkeypatch):
    """Test that facade methods properly delegate to specialized collectors."""
    import keyring

    monkeypatch.setattr(
        keyring, "get_password", lambda service, username: "dummy-token"
    )

    config = Config()
    collector = Collector(config)

    # Create a simple mock for api_client to avoid actual HTTP calls
    class MockApiClient:
        def request_list(self, path, params=None):
            return []

        def request_json(self, path, params=None):
            return {"login": "testuser"}

        def request_all(self, path, params=None):
            return []

        def paginate(self, path, base_params, per_page=100, early_stop=None):
            return []

    mock_client = MockApiClient()

    # Replace api_client in all collectors
    collector.api_client = mock_client
    collector.commit_collector.api_client = mock_client
    collector.pr_collector.api_client = mock_client
    collector.review_collector.api_client = mock_client
    collector.issue_collector.api_client = mock_client
    collector.analytics_collector.api_client = mock_client

    # Test facade methods don't crash
    from datetime import datetime, timezone

    since = datetime.now(timezone.utc)

    # These should delegate without errors
    assert collector.get_authenticated_user() == "testuser"
    assert collector.list_authored_pull_requests("test/repo", "user") == []
    assert collector.collect_commit_messages("test/repo", since) == []
    assert collector.collect_pr_titles("test/repo", since) == []
    assert collector.collect_issue_details("test/repo", since) == []
