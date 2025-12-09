"""Streak analysis for contribution consistency tracking."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from github_feedback.models import CollectionResult, StreakData


class StreakAnalyzer:
    """Analyzer for calculating contribution streaks and daily activity."""

    @staticmethod
    def analyze(
        daily_contributions: Dict[str, int],
        collection: Optional[CollectionResult] = None
    ) -> StreakData:
        """Analyze contribution streak data.

        Args:
            daily_contributions: Dictionary mapping date strings (YYYY-MM-DD) to contribution count
            collection: Optional collection result for additional context

        Returns:
            StreakData with streak information and badges
        """
        if not daily_contributions:
            return StreakData()

        # Sort dates
        sorted_dates = sorted(daily_contributions.keys())
        date_objects = [datetime.strptime(d, "%Y-%m-%d").date() for d in sorted_dates]

        # Calculate streaks
        current_streak = StreakAnalyzer._calculate_current_streak(date_objects)
        longest_streak = StreakAnalyzer._calculate_longest_streak(date_objects)
        total_active_days = len([count for count in daily_contributions.values() if count > 0])

        # Generate streak badges
        streak_badges = StreakAnalyzer._generate_streak_badges(
            current_streak, longest_streak, total_active_days
        )

        return StreakData(
            current_streak=current_streak,
            longest_streak=longest_streak,
            total_active_days=total_active_days,
            daily_contributions=daily_contributions,
            streak_badges=streak_badges,
        )

    @staticmethod
    def _calculate_current_streak(dates: List) -> int:
        """Calculate current consecutive contribution streak.

        Args:
            dates: Sorted list of date objects

        Returns:
            Number of consecutive days with contributions leading up to today
        """
        if not dates:
            return 0

        today = datetime.now().date()
        current_streak = 0

        # Check if the most recent contribution is today or yesterday
        most_recent = dates[-1]
        days_since_last = (today - most_recent).days

        if days_since_last > 1:
            # Streak is broken
            return 0

        # Count backwards from the most recent date
        for i in range(len(dates) - 1, 0, -1):
            expected_previous = dates[i] - timedelta(days=1)
            actual_previous = dates[i - 1]

            if actual_previous == expected_previous or actual_previous == dates[i]:
                current_streak += 1
            else:
                break

        # Add 1 for the most recent day
        current_streak += 1

        return current_streak

    @staticmethod
    def _calculate_longest_streak(dates: List) -> int:
        """Calculate longest consecutive contribution streak in the period.

        Args:
            dates: Sorted list of date objects

        Returns:
            Longest streak length
        """
        if not dates:
            return 0

        longest = 1
        current = 1

        for i in range(1, len(dates)):
            if dates[i] == dates[i - 1] + timedelta(days=1):
                current += 1
                longest = max(longest, current)
            elif dates[i] != dates[i - 1]:
                current = 1

        return longest

    @staticmethod
    def _generate_streak_badges(
        current_streak: int,
        longest_streak: int,
        total_active_days: int
    ) -> List[str]:
        """Generate streak-related achievement badges.

        Args:
            current_streak: Current streak length
            longest_streak: Longest streak length
            total_active_days: Total days with activity

        Returns:
            List of badge descriptions
        """
        badges = []

        # Current streak badges
        if current_streak >= 100:
            badges.append("🔥💯 백일 스트릭! 100일 연속 기여의 전설!")
        elif current_streak >= 50:
            badges.append("🔥🌟 오십일 스트릭! 불타는 열정!")
        elif current_streak >= 30:
            badges.append("🔥 30일 스트릭! 한 달 연속 기여!")
        elif current_streak >= 14:
            badges.append("🔥 2주 스트릭! 꾸준한 기여자!")
        elif current_streak >= 7:
            badges.append("🔥 1주 스트릭! 일주일 연속 기여!")

        # Longest streak badges (if different from current)
        if longest_streak != current_streak:
            if longest_streak >= 100:
                badges.append("⭐ 최장 스트릭 100일 이상!")
            elif longest_streak >= 50:
                badges.append("⭐ 최장 스트릭 50일 이상!")
            elif longest_streak >= 30:
                badges.append("⭐ 최장 스트릭 30일 이상!")

        # Activity frequency badges
        if total_active_days >= 200:
            badges.append("📅 200일 이상 활동한 초활동가!")
        elif total_active_days >= 100:
            badges.append("📅 100일 이상 활동한 활동가!")
        elif total_active_days >= 50:
            badges.append("📅 50일 이상 활동한 기여자!")

        return badges

    @staticmethod
    def build_from_monthly_trends(monthly_trends: List[Dict]) -> Dict[str, int]:
        """Build daily contributions from monthly trend data (placeholder).

        This is a simplified version that estimates daily distribution.
        For real data, you'd need actual commit timestamps from the collector.

        Args:
            monthly_trends: List of monthly trend dictionaries

        Returns:
            Dictionary mapping date strings to contribution counts
        """
        # This is a placeholder implementation
        # In reality, you'd need to modify the collector to track daily contributions
        daily_contributions: Dict[str, int] = defaultdict(int)

        # For now, return empty dict as we need actual daily data
        # TODO: Modify collector to track daily contributions
        return dict(daily_contributions)
