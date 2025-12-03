from datetime import datetime
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from github_feedback.analyzer import Analyzer
from github_feedback.models import (
    AnalysisFilters,
    CollectionResult,
    PullRequestSummary,
    DetailedFeedbackSnapshot,
    CommitFeedback,
    PRTitleFeedback,
    ReviewToneFeedback,
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


def test_witch_critique_checks_commit_quality():
    """Test that witch critique detects poor commit messages."""
    collection = CollectionResult(
        repo="example/repo",
        months=6,
        collected_at=datetime.utcnow(),
        commits=100,
        pull_requests=10,
        reviews=5,
        issues=3,
        filters=AnalysisFilters(),
        pull_request_examples=[],
    )

    # Create detailed feedback with poor commit messages
    detailed_feedback = DetailedFeedbackSnapshot(
        commit_feedback=CommitFeedback(
            total_commits=100,
            good_messages=20,
            poor_messages=80,  # 80% poor
            clear_messages=0,
        ),
    )

    analyzer = Analyzer()
    critique = analyzer._generate_witch_critique(collection, detailed_feedback)

    # Should have opening and closing
    assert critique.opening_curse
    assert critique.closing_prophecy

    # Should have at least one critique
    assert len(critique.critiques) > 0

    # Should have critique about commit messages
    assert any("커밋 메시지" in c.category for c in critique.critiques)


def test_witch_critique_checks_pr_size():
    """Test that witch critique detects oversized PRs."""
    collection = CollectionResult(
        repo="example/repo",
        months=6,
        collected_at=datetime.utcnow(),
        commits=100,
        pull_requests=10,
        reviews=5,
        issues=3,
        filters=AnalysisFilters(),
        pull_request_examples=[
            PullRequestSummary(
                number=1,
                title="Big PR",
                author="dev",
                html_url="https://github.com/example/repo/pull/1",
                created_at=datetime(2024, 1, 1),
                merged_at=datetime(2024, 1, 2),
                additions=5000,  # Very large PR
                deletions=3000,
            ),
            PullRequestSummary(
                number=2,
                title="Another big PR",
                author="dev",
                html_url="https://github.com/example/repo/pull/2",
                created_at=datetime(2024, 1, 3),
                merged_at=datetime(2024, 1, 4),
                additions=4000,
                deletions=2000,
            ),
        ],
    )

    analyzer = Analyzer()
    critique = analyzer._generate_witch_critique(collection, None)

    # Should have critique about PR size
    assert any("PR 크기" in c.category for c in critique.critiques)


def test_witch_critique_checks_pr_title_quality():
    """Test that witch critique detects vague PR titles."""
    collection = CollectionResult(
        repo="example/repo",
        months=6,
        collected_at=datetime.utcnow(),
        commits=100,
        pull_requests=10,
        reviews=5,
        issues=3,
        filters=AnalysisFilters(),
        pull_request_examples=[],
    )

    detailed_feedback = DetailedFeedbackSnapshot(
        pr_title_feedback=PRTitleFeedback(
            total_prs=10,
            clear_titles=2,
            vague_titles=8,  # 80% vague
        ),
    )

    analyzer = Analyzer()
    critique = analyzer._generate_witch_critique(collection, detailed_feedback)

    # Should have critique about PR titles
    assert any("PR 제목" in c.category for c in critique.critiques)


def test_witch_critique_checks_review_participation():
    """Test that witch critique detects low review participation."""
    collection = CollectionResult(
        repo="example/repo",
        months=6,
        collected_at=datetime.utcnow(),
        commits=100,
        pull_requests=50,  # Many PRs
        reviews=5,  # But few reviews
        issues=3,
        filters=AnalysisFilters(),
        pull_request_examples=[],
    )

    analyzer = Analyzer()
    critique = analyzer._generate_witch_critique(collection, None)

    # Should have critique about code review participation
    assert any("코드 리뷰" in c.category for c in critique.critiques)


def test_witch_critique_checks_activity_consistency():
    """Test that witch critique detects inconsistent activity."""
    collection = CollectionResult(
        repo="example/repo",
        months=12,  # 12 months
        collected_at=datetime.utcnow(),
        commits=24,  # Only 2 commits per month on average
        pull_requests=5,
        reviews=3,
        issues=1,
        filters=AnalysisFilters(),
        pull_request_examples=[],
    )

    analyzer = Analyzer()
    critique = analyzer._generate_witch_critique(collection, None)

    # Should have critique about activity consistency
    assert any("활동 일관성" in c.category for c in critique.critiques)


def test_witch_critique_always_returns_something():
    """Test that witch critique always returns at least one critique."""
    # Perfect developer with no issues
    collection = CollectionResult(
        repo="example/repo",
        months=6,
        collected_at=datetime.utcnow(),
        commits=600,  # Excellent activity
        pull_requests=50,
        reviews=50,  # Good review participation
        issues=10,
        filters=AnalysisFilters(),
        pull_request_examples=[
            PullRequestSummary(
                number=1,
                title="Well-sized PR",
                author="dev",
                html_url="https://github.com/example/repo/pull/1",
                created_at=datetime(2024, 1, 1),
                merged_at=datetime(2024, 1, 2),
                additions=100,  # Small, reasonable PR
                deletions=50,
            ),
        ],
    )

    detailed_feedback = DetailedFeedbackSnapshot(
        commit_feedback=CommitFeedback(
            total_commits=600,
            good_messages=600,  # All good
            poor_messages=0,
            clear_messages=0,
        ),
        pr_title_feedback=PRTitleFeedback(
            total_prs=50,
            clear_titles=50,  # All clear
            vague_titles=0,
        ),
        review_tone_feedback=ReviewToneFeedback(
            total_reviews=50,
            constructive_reviews=50,  # All constructive
            harsh_reviews=0,
            neutral_reviews=0,
        ),
    )

    analyzer = Analyzer()
    critique = analyzer._generate_witch_critique(collection, detailed_feedback)

    # Even with perfect metrics, should have a general advice critique
    assert len(critique.critiques) > 0
    assert critique.opening_curse
    assert critique.closing_prophecy

    # Should be a general advice critique
    assert critique.critiques[0].severity == "💫 조언"


def test_check_commit_message_quality_helper():
    """Test the helper method for checking commit message quality."""
    collection = CollectionResult(
        repo="example/repo",
        months=6,
        collected_at=datetime.utcnow(),
        commits=100,
        pull_requests=10,
        reviews=5,
        issues=3,
        filters=AnalysisFilters(),
        pull_request_examples=[],
    )

    detailed_feedback = DetailedFeedbackSnapshot(
        commit_feedback=CommitFeedback(
            total_commits=100,
            good_messages=20,
            poor_messages=80,
            clear_messages=0,
        ),
    )

    analyzer = Analyzer()
    critiques = []
    analyzer._check_commit_message_quality(detailed_feedback, critiques)

    assert len(critiques) == 1
    assert critiques[0].category == "커밋 메시지"
    assert critiques[0].severity == "🔥 치명적"


def test_check_pr_size_helper():
    """Test the helper method for checking PR size."""
    collection = CollectionResult(
        repo="example/repo",
        months=6,
        collected_at=datetime.utcnow(),
        commits=100,
        pull_requests=2,
        reviews=5,
        issues=3,
        filters=AnalysisFilters(),
        pull_request_examples=[
            PullRequestSummary(
                number=1,
                title="Big PR",
                author="dev",
                html_url="https://github.com/example/repo/pull/1",
                created_at=datetime(2024, 1, 1),
                merged_at=datetime(2024, 1, 2),
                additions=10000,
                deletions=5000,
            ),
            PullRequestSummary(
                number=2,
                title="Big PR 2",
                author="dev",
                html_url="https://github.com/example/repo/pull/2",
                created_at=datetime(2024, 1, 3),
                merged_at=datetime(2024, 1, 4),
                additions=8000,
                deletions=4000,
            ),
        ],
    )

    analyzer = Analyzer()
    critiques = []
    analyzer._check_pr_size(collection, critiques)

    assert len(critiques) == 1
    assert critiques[0].category == "PR 크기"
    assert critiques[0].severity == "⚡ 심각"


def test_get_random_general_critique():
    """Test that random general critique is valid."""
    collection = CollectionResult(
        repo="example/repo",
        months=6,
        collected_at=datetime.utcnow(),
        commits=100,
        pull_requests=10,
        reviews=5,
        issues=3,
        filters=AnalysisFilters(),
        pull_request_examples=[],
    )

    analyzer = Analyzer()
    critique = analyzer._get_random_general_critique(collection)

    assert critique.category
    assert critique.severity == "💫 조언"
    assert critique.critique
    assert critique.evidence
    assert critique.consequence
    assert critique.remedy
