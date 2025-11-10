from datetime import datetime
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from github_feedback.analyzer import Analyzer
from github_feedback.models import (
    AnalysisFilters,
    CollectionResult,
    PullRequestSummary,
)


def test_analyzer_generates_positive_metrics():
    collection = CollectionResult(
        repo="example/repo",
        months=6,
        collected_at=datetime.utcnow(),
        commits=120,
        pull_requests=30,
        reviews=25,
        issues=10,
        filters=AnalysisFilters(),
        pull_request_examples=[
            PullRequestSummary(
                number=101,
                title="Refactor core analytics",
                author="dev1",
                html_url="https://github.com/example/repo/pull/101",
                created_at=datetime(2024, 1, 15),
                merged_at=datetime(2024, 1, 20),
                additions=500,
                deletions=120,
            )
        ],
    )

    analyzer = Analyzer()
    metrics = analyzer.compute_metrics(collection)

    assert metrics.summary["velocity"].startswith("Average")
    assert metrics.stats["commits"]["per_month"] == collection.commits / collection.months
    assert metrics.evidence["commits"]
    assert metrics.highlights
    assert metrics.spotlight_examples["pull_requests"]
    assert metrics.yearbook_story
    assert metrics.awards
