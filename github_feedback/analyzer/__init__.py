"""Metric calculation logic for GitHub feedback analysis.

This is the refactored analyzer module. The main Analyzer class acts as an
orchestrator, delegating to specialized builders and analyzers.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, NamedTuple, Optional

from github_feedback.award_strategies import AwardCalculator
from github_feedback.console import Console
from github_feedback.models import (
    AnalysisStatus,
    CollectionResult,
    DetailedFeedbackSnapshot,
    MetricSnapshot,
)
from github_feedback.retrospective import RetrospectiveAnalyzer

from .builders import (
    EvidenceBuilder,
    FeedbackSnapshotBuilder,
    HighlightsBuilder,
    SpotlightExamplesBuilder,
    StatsBuilder,
    StoryBeatsBuilder,
    SummaryBuilder,
)
from .helpers import PeriodFormatter
from .trends import (
    CollaborationNetworkBuilder,
    MonthlyInsightsGenerator,
    MonthlyTrendsBuilder,
    TechStackAnalyzer,
)
from .witch_critique import WitchCritiqueGenerator
from .year_end import YearEndReviewBuilder

console = Console()


class CollectionStats(NamedTuple):
    """Statistics computed from collection data."""
    month_span: int
    velocity_score: float
    collaboration_score: float
    stability_score: int
    total_activity: int
    period_label: str


@dataclass(slots=True)
class Analyzer:
    """Transform collected data into actionable metrics.

    This class acts as an orchestrator, delegating specific tasks to
    specialized builders and analyzers for better separation of concerns.
    """

    web_base_url: str = "https://github.com"

    def compute_metrics(
        self,
        collection: CollectionResult,
        detailed_feedback: Optional[DetailedFeedbackSnapshot] = None,
        monthly_trends_data: Optional[List[Dict]] = None,
        tech_stack_data: Optional[Dict[str, int]] = None,
        collaboration_data: Optional[Dict[str, Any]] = None,
    ) -> MetricSnapshot:
        """Compute derived metrics from the collected artefacts.

        This method orchestrates the entire analysis process by delegating
        to specialized builders for different aspects of the analysis.
        """
        console.log("Analyzing repository trends", f"repo={collection.repo}")

        # Calculate basic statistics
        stats = self._calculate_scores(collection)

        # Build various metric components using specialized builders
        highlights = HighlightsBuilder.build(
            collection,
            stats.period_label,
            stats.month_span,
            stats.velocity_score,
            stats.total_activity,
        )

        spotlight_builder = SpotlightExamplesBuilder(self.web_base_url)
        spotlight_examples = spotlight_builder.build(collection)

        summary = SummaryBuilder.build(
            stats.period_label,
            stats.total_activity,
            stats.velocity_score,
            stats.collaboration_score,
            stats.stability_score,
        )

        story_beats = StoryBeatsBuilder.build(
            collection,
            stats.period_label,
            stats.total_activity
        )

        awards = self._determine_awards(collection)

        metric_stats = StatsBuilder.build(collection, stats.velocity_score)

        evidence_builder = EvidenceBuilder(self.web_base_url)
        evidence = evidence_builder.build(collection)

        # Build year-end specific insights
        monthly_trends = MonthlyTrendsBuilder.build(monthly_trends_data)
        monthly_insights = MonthlyInsightsGenerator.build(monthly_trends)
        tech_stack = TechStackAnalyzer.build(tech_stack_data)
        collaboration = CollaborationNetworkBuilder.build(collaboration_data)
        year_end_review = YearEndReviewBuilder.build(collection)

        # Generate witch's critique
        witch_generator = WitchCritiqueGenerator()
        witch_critique = witch_generator.generate(collection, detailed_feedback)

        # Create initial metrics snapshot
        metrics_snapshot = MetricSnapshot(
            repo=collection.repo,
            months=collection.months,
            generated_at=datetime.now(timezone.utc),
            status=AnalysisStatus.ANALYSED,
            summary=summary,
            stats=metric_stats,
            evidence=evidence,
            highlights=highlights,
            spotlight_examples=spotlight_examples,
            yearbook_story=story_beats,
            awards=awards,
            detailed_feedback=detailed_feedback,
            monthly_trends=monthly_trends,
            monthly_insights=monthly_insights,
            tech_stack=tech_stack,
            collaboration=collaboration,
            year_end_review=year_end_review,
            witch_critique=witch_critique,
            since_date=collection.since_date,
            until_date=collection.until_date,
        )

        # Generate comprehensive retrospective analysis
        console.log("Generating retrospective analysis", f"repo={collection.repo}")
        retrospective_analyzer = RetrospectiveAnalyzer()
        retrospective = retrospective_analyzer.analyze(metrics_snapshot)
        metrics_snapshot.retrospective = retrospective

        return metrics_snapshot

    def _calculate_scores(self, collection: CollectionResult) -> CollectionStats:
        """Calculate basic scores and statistics from collection data."""
        month_span = max(collection.months, 1)
        velocity_score = collection.commits / month_span
        collaboration_score = (collection.pull_requests + collection.reviews) / month_span
        stability_score = max(collection.commits - collection.issues, 0)
        total_activity = collection.commits + collection.pull_requests + collection.reviews
        period_label = PeriodFormatter.format_period(collection.months)

        return CollectionStats(
            month_span=month_span,
            velocity_score=velocity_score,
            collaboration_score=collaboration_score,
            stability_score=stability_score,
            total_activity=total_activity,
            period_label=period_label,
        )

    def _determine_awards(self, collection: CollectionResult) -> List[str]:
        """Determine awards based on collection metrics using Strategy pattern."""
        calculator = AwardCalculator()
        return calculator.determine_awards(collection)

    def build_detailed_feedback(
        self,
        commit_analysis: Optional[Dict] = None,
        pr_title_analysis: Optional[Dict] = None,
        review_tone_analysis: Optional[Dict] = None,
        issue_analysis: Optional[Dict] = None,
        personal_development_analysis: Optional[Dict] = None,
    ) -> DetailedFeedbackSnapshot:
        """Build detailed feedback snapshot from LLM analysis results."""
        return FeedbackSnapshotBuilder.build(
            commit_analysis,
            pr_title_analysis,
            review_tone_analysis,
            issue_analysis,
            personal_development_analysis,
        )


# Export the main class
__all__ = ["Analyzer"]
