"""Builders for detailed feedback snapshots."""

from __future__ import annotations

from typing import Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    pass

from github_feedback.core.models import (
    CommitMessageFeedback,
    DetailedFeedbackSnapshot,
    GrowthIndicator,
    ImprovementArea,
    IssueFeedback,
    PersonalDevelopmentAnalysis,
    PRTitleFeedback,
    ReviewToneFeedback,
    StrengthPoint,
)


class FeedbackSnapshotBuilder:
    """Build detailed feedback snapshot from LLM analysis results."""

    @staticmethod
    def build_commit_feedback(analysis: Dict) -> CommitMessageFeedback:
        """Build commit message feedback from analysis."""
        return CommitMessageFeedback(
            total_commits=analysis.get("good_messages", 0) + analysis.get("poor_messages", 0),
            good_messages=analysis.get("good_messages", 0),
            poor_messages=analysis.get("poor_messages", 0),
            suggestions=analysis.get("suggestions", []),
            examples_good=analysis.get("examples_good", []),
            examples_poor=analysis.get("examples_poor", []),
        )

    @staticmethod
    def build_pr_title_feedback(analysis: Dict) -> PRTitleFeedback:
        """Build PR title feedback from analysis."""
        return PRTitleFeedback(
            total_prs=analysis.get("clear_titles", 0) + analysis.get("vague_titles", 0),
            clear_titles=analysis.get("clear_titles", 0),
            vague_titles=analysis.get("vague_titles", 0),
            suggestions=analysis.get("suggestions", []),
            examples_good=analysis.get("examples_good", []),
            examples_poor=analysis.get("examples_poor", []),
        )

    @staticmethod
    def build_review_tone_feedback(analysis: Dict) -> ReviewToneFeedback:
        """Build review tone feedback from analysis."""
        return ReviewToneFeedback(
            total_reviews=analysis.get("constructive_reviews", 0)
            + analysis.get("harsh_reviews", 0)
            + analysis.get("neutral_reviews", 0),
            constructive_reviews=analysis.get("constructive_reviews", 0),
            harsh_reviews=analysis.get("harsh_reviews", 0),
            neutral_reviews=analysis.get("neutral_reviews", 0),
            suggestions=analysis.get("suggestions", []),
            examples_good=analysis.get("examples_good", []),
            examples_improve=analysis.get("examples_improve", []),
        )

    @staticmethod
    def build_issue_feedback(analysis: Dict) -> IssueFeedback:
        """Build issue feedback from analysis."""
        return IssueFeedback(
            total_issues=analysis.get("well_described", 0) + analysis.get("poorly_described", 0),
            well_described=analysis.get("well_described", 0),
            poorly_described=analysis.get("poorly_described", 0),
            suggestions=analysis.get("suggestions", []),
            examples_good=analysis.get("examples_good", []),
            examples_poor=analysis.get("examples_poor", []),
        )

    @staticmethod
    def build_personal_development_analysis(analysis: Dict) -> PersonalDevelopmentAnalysis:
        """Build personal development analysis from LLM response."""
        # Parse strengths
        strengths = []
        for strength_data in analysis.get("strengths", []):
            if not isinstance(strength_data, dict):
                continue
            strengths.append(
                StrengthPoint(
                    category=strength_data.get("category", ""),
                    description=strength_data.get("description", ""),
                    evidence=strength_data.get("evidence", []),
                    impact=strength_data.get("impact", "medium"),
                )
            )

        # Parse improvement areas
        improvement_areas = []
        for improvement_data in analysis.get("improvement_areas", []):
            if not isinstance(improvement_data, dict):
                continue
            improvement_areas.append(
                ImprovementArea(
                    category=improvement_data.get("category", ""),
                    description=improvement_data.get("description", ""),
                    evidence=improvement_data.get("evidence", []),
                    suggestions=improvement_data.get("suggestions", []),
                    priority=improvement_data.get("priority", "medium"),
                )
            )

        # Parse growth indicators
        growth_indicators = []
        for growth_data in analysis.get("growth_indicators", []):
            if not isinstance(growth_data, dict):
                continue
            growth_indicators.append(
                GrowthIndicator(
                    aspect=growth_data.get("aspect", ""),
                    description=growth_data.get("description", ""),
                    before_examples=growth_data.get("before_examples", []),
                    after_examples=growth_data.get("after_examples", []),
                    progress_summary=growth_data.get("progress_summary", ""),
                )
            )

        return PersonalDevelopmentAnalysis(
            strengths=strengths,
            improvement_areas=improvement_areas,
            growth_indicators=growth_indicators,
            overall_assessment=analysis.get("overall_assessment", ""),
            key_achievements=analysis.get("key_achievements", []),
            next_focus_areas=analysis.get("next_focus_areas", []),
        )

    @staticmethod
    def build(
        commit_analysis: Optional[Dict] = None,
        pr_title_analysis: Optional[Dict] = None,
        review_tone_analysis: Optional[Dict] = None,
        issue_analysis: Optional[Dict] = None,
        personal_development_analysis: Optional[Dict] = None,
    ) -> DetailedFeedbackSnapshot:
        """Build detailed feedback snapshot from LLM analysis results."""
        return DetailedFeedbackSnapshot(
            commit_feedback=FeedbackSnapshotBuilder.build_commit_feedback(commit_analysis) if commit_analysis else None,
            pr_title_feedback=FeedbackSnapshotBuilder.build_pr_title_feedback(pr_title_analysis) if pr_title_analysis else None,
            review_tone_feedback=FeedbackSnapshotBuilder.build_review_tone_feedback(review_tone_analysis) if review_tone_analysis else None,
            issue_feedback=FeedbackSnapshotBuilder.build_issue_feedback(issue_analysis) if issue_analysis else None,
            personal_development=FeedbackSnapshotBuilder.build_personal_development_analysis(personal_development_analysis) if personal_development_analysis else None,
        )
