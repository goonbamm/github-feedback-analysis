"""Tests for CLI helper task orchestration."""

from __future__ import annotations

import time

from github_feedback.cli import helpers
from github_feedback.core.constants import TaskType


def test_run_parallel_tasks_continues_when_single_task_times_out(monkeypatch) -> None:
    """One timed-out task should not prevent other task results from being returned."""
    monkeypatch.setattr(helpers, "Progress", None)

    def fast_task() -> str:
        return "ok"

    def slow_task() -> list:
        time.sleep(0.2)
        return ["too-late"]

    tasks = {
        "fast": (fast_task, (), "Fast task"),
        "slow": (slow_task, (), "Slow task"),
    }

    results = helpers.run_parallel_tasks(
        tasks=tasks,
        max_workers=2,
        timeout=0.05,
        task_type=TaskType.COLLECTION,
    )

    assert results["fast"] == "ok"
    assert results["slow"] == []


def test_run_parallel_tasks_uses_timeout_error_path_for_timed_out_future(monkeypatch) -> None:
    """Timed-out futures should be normalized through handle_task_exception TimeoutError path."""
    monkeypatch.setattr(helpers, "Progress", None)

    observed_exception_types: list[type[Exception]] = []
    original_handler = helpers.handle_task_exception

    def tracking_handler(exception, key, label, timeout, task_type):
        observed_exception_types.append(type(exception))
        return original_handler(exception, key, label, timeout, task_type)

    monkeypatch.setattr(helpers, "handle_task_exception", tracking_handler)

    def slow_analysis() -> str:
        time.sleep(0.2)
        return "late"

    results = helpers.run_parallel_tasks(
        tasks={"analysis": (slow_analysis, (), "Slow analysis")},
        max_workers=1,
        timeout=0.05,
        task_type=TaskType.ANALYSIS,
    )

    assert results["analysis"] is None
    assert TimeoutError in observed_exception_types
