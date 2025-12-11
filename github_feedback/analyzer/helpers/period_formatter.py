"""Format period labels based on month count."""

from __future__ import annotations


class PeriodFormatter:
    """Format period labels based on month count."""

    # Mapping of common month counts to Korean labels
    LABEL_MAP = {
        3: "최근 3개월",
        6: "최근 6개월",
        12: "최근 1년",
    }

    @staticmethod
    def format_period(months: int) -> str:
        """Format period label based on month count.

        Args:
            months: Number of months in the period

        Returns:
            Formatted period label in Korean

        Examples:
            >>> PeriodFormatter.format_period(3)
            '최근 3개월'
            >>> PeriodFormatter.format_period(12)
            '최근 1년'
            >>> PeriodFormatter.format_period(25)
            '최근 2년 1개월'
        """
        # Check for exact matches first
        if months in PeriodFormatter.LABEL_MAP:
            return PeriodFormatter.LABEL_MAP[months]

        # Handle years and remaining months
        from github_feedback.core.constants import MONTHS_FOR_YEAR_DISPLAY, MONTHS_PER_YEAR
        if months >= MONTHS_FOR_YEAR_DISPLAY:
            years = months // MONTHS_PER_YEAR
            remaining_months = months % MONTHS_PER_YEAR
            if remaining_months == 0:
                return f"최근 {years}년"
            return f"최근 {years}년 {remaining_months}개월"

        # Default to months
        return f"최근 {months}개월"
