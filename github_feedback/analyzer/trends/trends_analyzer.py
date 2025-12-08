"""Monthly trends analysis for GitHub activity."""

from __future__ import annotations

import math
from typing import Dict, List, Optional

from github_feedback.constants import (
    ACTIVITY_THRESHOLDS,
    CONSISTENCY_THRESHOLDS,
    DISPLAY_LIMITS,
    TREND_THRESHOLDS,
)
from github_feedback.models import (
    CollaborationNetwork,
    MonthlyTrend,
    MonthlyTrendInsights,
    TechStackAnalysis,
)


class MonthlyTrendsBuilder:
    """Build monthly trend objects from raw data."""

    @staticmethod
    def build(monthly_trends_data: Optional[List[Dict]]) -> List[MonthlyTrend]:
        """Build monthly trend objects from raw data."""
        if not monthly_trends_data:
            return []

        trends = []
        for data in monthly_trends_data:
            trends.append(
                MonthlyTrend(
                    month=data.get("month", ""),
                    commits=data.get("commits", 0),
                    pull_requests=data.get("pull_requests", 0),
                    reviews=data.get("reviews", 0),
                    issues=data.get("issues", 0),
                )
            )
        return trends


class TrendAnalyzer:
    """Analyze trends in activity data."""

    @staticmethod
    def calculate_trend_direction(monthly_activities: List[tuple]) -> str:
        """Calculate trend direction from monthly activities.

        Algorithm:
        1. Requires minimum number of months (from TREND_THRESHOLDS)
        2. Splits activity data into two halves (early vs recent)
        3. Compares average activity between halves
        4. Returns 'increasing' if recent > early * multiplier
        5. Returns 'decreasing' if recent < early * multiplier
        6. Returns 'stable' otherwise

        Args:
            monthly_activities: List of (month, activity_count) tuples

        Returns:
            One of: "increasing", "decreasing", or "stable"
        """
        if len(monthly_activities) < TREND_THRESHOLDS['minimum_months_for_trend']:
            return "stable"

        recent_half = monthly_activities[len(monthly_activities)//2:]
        early_half = monthly_activities[:len(monthly_activities)//2]

        recent_avg = sum(act for _, act in recent_half) / len(recent_half) if recent_half else 0
        early_avg = sum(act for _, act in early_half) / len(early_half) if early_half else 0

        if recent_avg > early_avg * TREND_THRESHOLDS['increasing_multiplier']:
            return "increasing"
        elif recent_avg < early_avg * TREND_THRESHOLDS['decreasing_multiplier']:
            return "decreasing"
        else:
            return "stable"

    @staticmethod
    def calculate_consistency_score(monthly_activities: List[tuple]) -> float:
        """Calculate consistency score from monthly activities.

        Uses coefficient of variation (CV) to measure consistency:
        - CV = standard_deviation / mean
        - Lower CV indicates more consistent activity
        - Returns score from 0 (highly variable) to 1 (perfectly consistent)
        """
        activities = [act for _, act in monthly_activities if act > 0]
        if not activities or len(activities) < 2:
            return 0.0

        mean_activity = sum(activities) / len(activities)
        variance = sum((act - mean_activity) ** 2 for act in activities) / len(activities)
        std_dev = math.sqrt(variance)

        # Coefficient of variation (lower is more consistent)
        cv = std_dev / mean_activity if mean_activity > 0 else 1.0
        # Convert to 0-1 score (1 = perfect consistency, 0 = highly variable)
        return max(0.0, 1.0 - min(cv, 1.0))

    @staticmethod
    def generate_trend_insights(
        monthly_trends: List[MonthlyTrend],
        monthly_activities: List[tuple],
        peak_month: Optional[str],
        quiet_month: Optional[str],
        trend_direction: str,
        consistency_score: float,
    ) -> List[str]:
        """Generate human-readable insights from trend data."""
        insights = []

        if peak_month:
            peak_activity = next((act for month, act in monthly_activities if month == peak_month), 0)
            insights.append(
                f"{peak_month}에 가장 활발했습니다 (총 {peak_activity}건의 활동)"
            )

        if quiet_month and quiet_month != peak_month:
            quiet_activity = next((act for month, act in monthly_activities if month == quiet_month), 0)
            insights.append(
                f"{quiet_month}에는 상대적으로 조용했습니다 (총 {quiet_activity}건의 활동)"
            )

        if trend_direction == "increasing":
            insights.append(
                "시간이 지날수록 활동량이 증가하는 성장 추세를 보였습니다"
            )
        elif trend_direction == "decreasing":
            insights.append(
                "최근 활동량이 감소하는 경향이 있습니다. 새로운 동기 부여가 필요할 수 있습니다"
            )
        else:
            insights.append(
                "꾸준한 활동 수준을 유지했습니다"
            )

        if consistency_score > CONSISTENCY_THRESHOLDS['very_consistent']:
            insights.append(
                f"매우 일관된 활동 패턴을 보였습니다 (일관성 점수: {consistency_score:.1%})"
            )
        elif consistency_score < CONSISTENCY_THRESHOLDS['inconsistent']:
            insights.append(
                f"활동량의 변동이 큰 편입니다 (일관성 점수: {consistency_score:.1%}). "
                "더 균형잡힌 기여 리듬을 만들어보세요"
            )

        # Analyze specific activity types
        commits_trend = [trend.commits for trend in monthly_trends]
        prs_trend = [trend.pull_requests for trend in monthly_trends]

        if commits_trend and max(commits_trend) > 0:
            peak_commit_month = monthly_trends[commits_trend.index(max(commits_trend))].month
            insights.append(
                f"커밋 활동은 {peak_commit_month}에 정점을 찍었습니다 ({max(commits_trend)}회)"
            )

        if prs_trend and max(prs_trend) > 0:
            peak_pr_month = monthly_trends[prs_trend.index(max(prs_trend))].month
            if max(prs_trend) >= ACTIVITY_THRESHOLDS['moderate_prs']:
                insights.append(
                    f"PR 활동은 {peak_pr_month}에 가장 왕성했습니다 ({max(prs_trend)}개)"
                )

        return insights


class MonthlyInsightsGenerator:
    """Generate insights from monthly trends."""

    @staticmethod
    def build(monthly_trends: List[MonthlyTrend]) -> Optional[MonthlyTrendInsights]:
        """Analyze monthly trends and generate insights."""
        if not monthly_trends or len(monthly_trends) < 2:
            return None

        # Calculate total activity per month
        monthly_activities = [
            (trend.month, trend.commits + trend.pull_requests + trend.reviews + trend.issues)
            for trend in monthly_trends
        ]

        # Find peak and quiet months
        peak_month_data = max(monthly_activities, key=lambda x: x[1])
        peak_month = peak_month_data[0] if peak_month_data[1] > 0 else None

        non_zero_activities = [(month, activity) for month, activity in monthly_activities if activity > 0]
        quiet_month = None
        if non_zero_activities:
            quiet_month_data = min(non_zero_activities, key=lambda x: x[1])
            quiet_month = quiet_month_data[0]

        # Calculate active months
        total_active_months = sum(1 for _, activity in monthly_activities if activity > 0)

        # Calculate metrics
        trend_direction = TrendAnalyzer.calculate_trend_direction(monthly_activities)
        consistency_score = TrendAnalyzer.calculate_consistency_score(monthly_activities)

        # Generate insights
        insights = TrendAnalyzer.generate_trend_insights(
            monthly_trends,
            monthly_activities,
            peak_month,
            quiet_month,
            trend_direction,
            consistency_score,
        )

        return MonthlyTrendInsights(
            peak_month=peak_month,
            quiet_month=quiet_month,
            trend_direction=trend_direction,
            total_active_months=total_active_months,
            consistency_score=consistency_score,
            insights=insights,
        )


class TechStackAnalyzer:
    """Analyze technology stack from file changes."""

    @staticmethod
    def build(tech_stack_data: Optional[Dict[str, int]]) -> Optional[TechStackAnalysis]:
        """Analyze technology stack from file changes."""
        if not tech_stack_data:
            return None

        # Calculate top languages
        sorted_languages = sorted(
            tech_stack_data.items(), key=lambda x: x[1], reverse=True
        )
        top_languages = [lang for lang, _ in sorted_languages[:DISPLAY_LIMITS['top_languages']]]

        # Calculate diversity score (Shannon entropy normalized)
        total_files = sum(tech_stack_data.values())
        if total_files == 0:
            diversity_score = 0.0
        else:
            entropy = 0.0
            for count in tech_stack_data.values():
                if count > 0:
                    p = count / total_files
                    entropy -= p * math.log2(p)
            # Normalize to 0-1 range (max entropy is log2(n))
            max_entropy = math.log2(len(tech_stack_data)) if len(tech_stack_data) > 1 else 1
            diversity_score = entropy / max_entropy if max_entropy > 0 else 0.0

        return TechStackAnalysis(
            languages=tech_stack_data,
            top_languages=top_languages,
            diversity_score=diversity_score,
        )


class CollaborationNetworkBuilder:
    """Build collaboration network from reviewer data."""

    @staticmethod
    def build(collaboration_data: Optional[Dict]) -> Optional[CollaborationNetwork]:
        """Build collaboration network from reviewer data."""
        if not collaboration_data:
            return None

        pr_reviewers = collaboration_data.get("pr_reviewers", {})
        sorted_reviewers = sorted(
            pr_reviewers.items(), key=lambda x: x[1], reverse=True
        )
        top_reviewers = [reviewer for reviewer, _ in sorted_reviewers[:DISPLAY_LIMITS['top_reviewers']]]

        return CollaborationNetwork(
            pr_reviewers=pr_reviewers,
            top_reviewers=top_reviewers,
            review_received_count=collaboration_data.get("review_received_count", 0),
            unique_collaborators=collaboration_data.get("unique_collaborators", 0),
        )
