from datetime import datetime
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from github_feedback.analyzer import Analyzer
from github_feedback.models import AnalysisFilters, CollectionResult


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
    )

    analyzer = Analyzer()
    metrics = analyzer.compute_metrics(collection)

    assert metrics.summary["velocity"].startswith("Average")
    assert metrics.stats["commits"]["per_month"] == collection.commits / collection.months
    assert metrics.evidence["commits"]
