"""Statistics calculation for review reports."""

from __future__ import annotations

from typing import List

from ..constants import (
    STAT_WEIGHTS_CODE_QUALITY,
    STAT_WEIGHTS_COLLABORATION,
    STAT_WEIGHTS_GROWTH,
    STAT_WEIGHTS_PROBLEM_SOLVING,
    STAT_WEIGHTS_PRODUCTIVITY,
)
from .data_loader import StoredReview


class ReviewStatsCalculator:
    """Calculate RPG-style character stats from PR reviews."""

    @staticmethod
    def calculate_character_stats(reviews: List[StoredReview]) -> dict:
        """Calculate RPG-style character stats from PR reviews."""
        if not reviews:
            return {
                "code_quality": 0,
                "collaboration": 0,
                "problem_solving": 0,
                "productivity": 0,
                "growth": 0,
            }

        total_prs = len(reviews)
        total_additions = sum(r.additions for r in reviews)
        total_deletions = sum(r.deletions for r in reviews)
        total_files = sum(r.changed_files for r in reviews)
        total_strengths = sum(len(r.strengths) for r in reviews)
        total_improvements = sum(len(r.improvements) for r in reviews)

        # Code Quality (0-100): Based on strength ratio and file organization
        code_quality = ReviewStatsCalculator._calculate_code_quality(
            total_prs, total_files, total_strengths, total_improvements
        )

        # Collaboration (0-100): Based on review engagement
        collaboration = ReviewStatsCalculator._calculate_collaboration(
            reviews, total_prs, total_strengths, total_improvements
        )

        # Problem Solving (0-100): Based on PR complexity and scope
        problem_solving = ReviewStatsCalculator._calculate_problem_solving(
            total_prs, total_additions, total_deletions, total_files
        )

        # Productivity (0-100): Based on output volume
        productivity = ReviewStatsCalculator._calculate_productivity(
            total_prs, total_additions, total_files
        )

        # Growth (0-100): Based on consistent improvement
        growth = ReviewStatsCalculator._calculate_growth(reviews)

        return {
            "code_quality": code_quality,
            "collaboration": collaboration,
            "problem_solving": problem_solving,
            "productivity": productivity,
            "growth": growth,
        }

    @staticmethod
    def _calculate_code_quality(
        total_prs: int, total_files: int, total_strengths: int, total_improvements: int
    ) -> int:
        """Calculate code quality stat."""
        avg_files_per_pr = total_files / total_prs if total_prs > 0 else 0
        strength_ratio = total_strengths / max(total_strengths + total_improvements, 1)

        w_cq = STAT_WEIGHTS_CODE_QUALITY
        code_quality = min(
            100,
            int(
                (strength_ratio * w_cq["strength_contribution"])
                + (min(avg_files_per_pr / w_cq["optimal_files_per_pr"], 1) * w_cq["file_organization"])
                + (
                    w_cq["experience_bonus"]
                    if total_prs >= w_cq["experience_pr_threshold"]
                    else (total_prs / w_cq["experience_pr_threshold"]) * w_cq["experience_bonus"]
                )
            ),
        )
        return code_quality

    @staticmethod
    def _calculate_collaboration(
        reviews: List[StoredReview], total_prs: int, total_strengths: int, total_improvements: int
    ) -> int:
        """Calculate collaboration stat."""
        has_reviews = sum(1 for r in reviews if r.review_bodies or r.review_comments)
        collaboration_rate = has_reviews / total_prs if total_prs > 0 else 0
        avg_feedback = (total_strengths + total_improvements) / total_prs if total_prs > 0 else 0

        w_col = STAT_WEIGHTS_COLLABORATION
        collaboration = min(
            100,
            int(
                (collaboration_rate * w_col["review_engagement"])
                + (min(avg_feedback / w_col["optimal_feedback_per_pr"], 1) * w_col["feedback_quality"])
                + (
                    w_col["participation_bonus"]
                    if total_prs >= w_col["participation_pr_threshold"]
                    else (total_prs / w_col["participation_pr_threshold"]) * w_col["participation_bonus"]
                )
            ),
        )
        return collaboration

    @staticmethod
    def _calculate_problem_solving(
        total_prs: int, total_additions: int, total_deletions: int, total_files: int
    ) -> int:
        """Calculate problem solving stat."""
        avg_changes = (total_additions + total_deletions) / total_prs if total_prs > 0 else 0
        avg_files_per_pr = total_files / total_prs if total_prs > 0 else 0

        w_ps = STAT_WEIGHTS_PROBLEM_SOLVING
        problem_solving = min(
            100,
            int(
                (min(avg_changes / w_ps["optimal_changes_per_pr"], 1) * w_ps["change_complexity"])
                + (min(avg_files_per_pr / w_ps["optimal_files_per_pr"], 1) * w_ps["scope_breadth"])
                + (
                    w_ps["problem_count"]
                    if total_prs >= w_ps["problem_pr_threshold"]
                    else (total_prs / w_ps["problem_pr_threshold"]) * w_ps["problem_count"]
                )
            ),
        )
        return problem_solving

    @staticmethod
    def _calculate_productivity(total_prs: int, total_additions: int, total_files: int) -> int:
        """Calculate productivity stat."""
        w_prod = STAT_WEIGHTS_PRODUCTIVITY
        productivity = min(
            100,
            int(
                (min(total_prs / w_prod["optimal_pr_count"], 1) * w_prod["pr_count"])
                + (min(total_additions / w_prod["optimal_additions"], 1) * w_prod["code_output"])
                + (min(total_files / w_prod["optimal_file_count"], 1) * w_prod["file_coverage"])
            ),
        )
        return productivity

    @staticmethod
    def _calculate_growth(reviews: List[StoredReview]) -> int:
        """Calculate growth stat."""
        total_prs = len(reviews)
        w_growth = STAT_WEIGHTS_GROWTH

        if total_prs >= w_growth["min_prs_for_trend"]:
            mid_point = total_prs // 2
            first_half = reviews[:mid_point]
            second_half = reviews[mid_point:]

            first_avg_strengths = sum(len(r.strengths) for r in first_half) / len(first_half)
            second_avg_strengths = sum(len(r.strengths) for r in second_half) / len(second_half)

            improvement_rate = (second_avg_strengths - first_avg_strengths) / max(first_avg_strengths, 1)
            growth = min(
                100,
                max(
                    0,
                    int(
                        w_growth["base_growth"]
                        + (improvement_rate * w_growth["improvement_trend"])
                        + (
                            w_growth["consistency_bonus"]
                            if total_prs >= w_growth["consistency_pr_threshold"]
                            else (total_prs / w_growth["consistency_pr_threshold"])
                            * w_growth["consistency_bonus"]
                        )
                    ),
                ),
            )
        else:
            # Base growth for new developers
            growth = min(
                100,
                int(
                    (total_prs / w_growth["min_prs_for_trend"]) * w_growth["new_developer_multiplier"]
                    + w_growth["new_developer_base"]
                ),
            )

        return growth


__all__ = ["ReviewStatsCalculator"]
