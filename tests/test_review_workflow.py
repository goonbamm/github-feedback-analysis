"""Integration style tests for the pull request review helpers."""

from __future__ import annotations

import json as jsonlib
from datetime import datetime, timezone

import pytest

requests = pytest.importorskip("requests")

from github_feedback.collector import Collector
from github_feedback.config import AuthConfig, Config
from github_feedback.models import PullRequestFile, PullRequestReviewBundle, ReviewPoint, ReviewSummary
from github_feedback.reviewer import Reviewer
from github_feedback.llm import (
    LLMClient,
    MAX_FILES_WITH_PATCH_SNIPPETS,
    MAX_PATCH_LINES_PER_FILE,
)


class DummyLLM:
    """Deterministic LLM stand-in used for tests."""

    def generate_review(self, bundle: PullRequestReviewBundle) -> ReviewSummary:  # noqa: D401 - simple stub
        return ReviewSummary(
            overview=(
                f"Pull request #{bundle.number} touches {bundle.changed_files} files "
                f"with {bundle.additions} additions and {bundle.deletions} deletions."
            ),
            strengths=[
                ReviewPoint(
                    message="Well structured change set.",
                    example=bundle.files[0].filename if bundle.files else None,
                )
            ],
            improvements=[
                ReviewPoint(
                    message="Consider adding regression tests.",
                    example=bundle.review_comments[0] if bundle.review_comments else None,
                )
            ],
        )


def _make_bundle() -> PullRequestReviewBundle:
    now = datetime.now(timezone.utc)
    return PullRequestReviewBundle(
        repo="example/repo",
        number=7,
        title="Improve data caching",
        body="Adds persistent caching for review data.",
        author="octocat",
        html_url="https://github.com/example/repo/pull/7",
        created_at=now,
        updated_at=now,
        additions=120,
        deletions=30,
        changed_files=2,
        review_bodies=["LGTM"],
        review_comments=["Nit: adjust variable naming."],
        files=[
            PullRequestFile(
                filename="cache.py",
                status="modified",
                additions=100,
                deletions=10,
                changes=110,
                patch="@@ -1,3 +1,3 @@\n-print('old')\n+print('new')",
            ),
            PullRequestFile(
                filename="tests/test_cache.py",
                status="added",
                additions=20,
                deletions=0,
                changes=20,
                patch="@@ -0,0 +1,2 @@\n+assert True",
            ),
        ],
    )


def test_collect_pull_request_details_gathers_expected_fields(monkeypatch):
    config = Config(auth=AuthConfig(pat="dummy"))
    collector = Collector(config)

    pr_payload = {
        "title": "Improve data caching",
        "body": "Adds persistent caching for review data.",
        "user": {"login": "octocat"},
        "html_url": "https://github.com/example/repo/pull/7",
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T01:00:00Z",
        "additions": 120,
        "deletions": 30,
        "changed_files": 2,
    }

    def fake_request(path: str, params=None):  # type: ignore[override]
        if path.endswith("/reviews"):
            return [{"body": "Looks good"}]
        if path.endswith("/comments"):
            return [{"body": "Nit: adjust variable naming."}]
        if path.endswith("/files"):
            return [
                {
                    "filename": "cache.py",
                    "status": "modified",
                    "additions": 100,
                    "deletions": 10,
                    "changes": 110,
                    "patch": "@@ -1 +1 @@",
                }
            ]
        raise AssertionError(f"Unhandled path: {path}")

    def fake_request_json(path: str, params=None):  # type: ignore[override]
        assert path.endswith("/pulls/7")
        return pr_payload

    monkeypatch.setattr(collector, "_request", fake_request)
    monkeypatch.setattr(collector, "_request_json", fake_request_json)

    bundle = collector.collect_pull_request_details("example/repo", 7)

    assert bundle.title == "Improve data caching"
    assert bundle.review_comments == ["Nit: adjust variable naming."]
    assert bundle.review_bodies == ["Looks good"]
    assert bundle.files[0].filename == "cache.py"


def test_reviewer_persists_outputs(tmp_path, monkeypatch):
    bundle = _make_bundle()

    class DummyCollector:
        def collect_pull_request_details(self, repo: str, number: int) -> PullRequestReviewBundle:  # noqa: D401 - simple stub
            assert repo == bundle.repo
            assert number == bundle.number
            return bundle

    reviewer = Reviewer(collector=DummyCollector(), llm=DummyLLM(), output_dir=tmp_path)

    pr_title, artefact_path, summary_path, markdown_path = reviewer.review_pull_request(
        repo=bundle.repo,
        number=bundle.number,
    )

    assert pr_title == bundle.title

    assert artefact_path.exists()
    assert summary_path.exists()
    assert markdown_path.exists()

    assert artefact_path.is_relative_to(tmp_path)
    assert summary_path.is_relative_to(tmp_path)
    assert markdown_path.is_relative_to(tmp_path)

    artefacts = artefact_path.read_text(encoding="utf-8")
    summary = summary_path.read_text(encoding="utf-8")
    markdown = markdown_path.read_text(encoding="utf-8")

    assert "cache.py" in artefacts
    assert "Pull request #7" in summary
    assert "## Strengths" in markdown
    assert "## Areas To Improve" in markdown


def test_llm_client_falls_back_when_json_object_not_supported(monkeypatch):
    bundle = _make_bundle()
    client = LLMClient(endpoint="https://llm.example.com", model="dummy-model")

    responses = []

    class DummyResponse:
        def __init__(self, status_code: int, payload: dict, text: str = "") -> None:
            self.status_code = status_code
            self._payload = payload
            self.text = text

        def raise_for_status(self) -> None:
            if self.status_code >= 400:
                exc = requests.HTTPError(response=self)
                raise exc

        def json(self) -> dict:
            return self._payload

    def fake_post(url, json=None, timeout=None):  # type: ignore[override]
        responses.append(json)
        if json and "response_format" in json:
            return DummyResponse(
                400,
                payload={"error": {"message": "type 'json_object' not supported"}},
                text="type 'json_object' not supported",
            )
        payload = {
            "choices": [
                {
                    "message": {
                        "content": jsonlib.dumps(
                            {
                                "overview": "Looks good.",
                                "strengths": [],
                                "improvements": [],
                            }
                        )
                    }
                }
            ]
        }
        return DummyResponse(200, payload)

    monkeypatch.setattr("requests.post", fake_post)

    summary = client.generate_review(bundle)

    assert summary.overview == "Looks good."
    assert len(responses) == 2
    assert "response_format" in responses[0]
    assert "response_format" not in responses[1]


def test_llm_client_retries_after_server_error(monkeypatch):
    bundle = _make_bundle()
    client = LLMClient(endpoint="https://llm.example.com", model="dummy-model")

    responses = []

    class DummyResponse:
        def __init__(self, status_code: int, payload: dict, text: str = "") -> None:
            self.status_code = status_code
            self._payload = payload
            self.text = text

        def raise_for_status(self) -> None:
            if self.status_code >= 400:
                raise requests.HTTPError(response=self)

        def json(self) -> dict:
            return self._payload

    def fake_post(url, json=None, timeout=None):  # type: ignore[override]
        responses.append(json)
        if len(responses) == 1:
            return DummyResponse(
                500,
                payload={"error": {"message": "failed to advance FSM for request"}},
                text="failed to advance FSM for request",
            )
        payload = {
            "choices": [
                {
                    "message": {
                        "content": jsonlib.dumps(
                            {
                                "overview": "Looks good.",
                                "strengths": [],
                                "improvements": [],
                            }
                        )
                    }
                }
            ]
        }
        return DummyResponse(200, payload)

    monkeypatch.setattr("requests.post", fake_post)

    summary = client.generate_review(bundle)

    assert summary.overview == "Looks good."
    assert len(responses) == 2
    assert "response_format" in responses[0]
    assert "response_format" not in responses[1]


def test_llm_client_retries_when_content_not_json(monkeypatch):
    bundle = _make_bundle()
    client = LLMClient(endpoint="https://llm.example.com", model="dummy-model")

    responses = []

    class DummyResponse:
        def __init__(self, status_code: int, payload: dict) -> None:
            self.status_code = status_code
            self._payload = payload
            self.text = ""

        def raise_for_status(self) -> None:
            if self.status_code >= 400:
                raise requests.HTTPError(response=self)

        def json(self) -> dict:
            return self._payload

    def fake_post(url, json=None, timeout=None):  # type: ignore[override]
        responses.append(json)
        if len(responses) == 1:
            payload = {
                "choices": [
                    {
                        "message": {
                            "content": "not valid json"
                        }
                    }
                ]
            }
            return DummyResponse(200, payload)
        payload = {
            "choices": [
                {
                    "message": {
                        "content": jsonlib.dumps(
                            {
                                "overview": "Looks good.",
                                "strengths": [],
                                "improvements": [],
                            }
                        )
                    }
                }
            ]
        }
        return DummyResponse(200, payload)

    monkeypatch.setattr("requests.post", fake_post)

    summary = client.generate_review(bundle)

    assert summary.overview == "Looks good."
    assert len(responses) == 2
    assert "response_format" in responses[0]
    assert "response_format" not in responses[1]


def test_llm_prompt_includes_truncated_diff_snippets():
    bundle = _make_bundle()
    long_patch_lines = ["@@ -1 +1 @@"] + [f"+line {idx}" for idx in range(1, 31)]
    long_patch = "\n".join(long_patch_lines)

    files = []
    for idx in range(7):
        files.append(
            PullRequestFile(
                filename=f"module{idx}.py",
                status="modified",
                additions=idx + 1,
                deletions=0,
                changes=idx + 1,
                patch=long_patch if idx == 0 else "@@ -0,0 +1 @@\n+short",
            )
        )

    bundle.files = files
    bundle.changed_files = len(files)

    client = LLMClient(endpoint="https://llm.example.com", model="dummy-model")
    messages = client._build_messages(bundle)
    prompt = messages[1]["content"]

    assert prompt.count("```diff") == min(MAX_FILES_WITH_PATCH_SNIPPETS, len(files))

    first_snippet = prompt.split("```diff", 1)[1].split("```", 1)[0]
    last_visible_line = MAX_PATCH_LINES_PER_FILE - 2
    assert f"line {last_visible_line}" in first_snippet
    assert f"line {last_visible_line + 5}" not in first_snippet
    assert "..." in first_snippet

    trailing_section = prompt.split(f"- {files[MAX_FILES_WITH_PATCH_SNIPPETS].filename}", 1)[1]
    assert "```diff" not in trailing_section
