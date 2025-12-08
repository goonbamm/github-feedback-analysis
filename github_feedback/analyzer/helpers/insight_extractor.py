"""Helper class for extracting insights from PR collections."""

from __future__ import annotations

from typing import Optional


class InsightExtractor:
    """Helper class for extracting insights from PR collections."""

    @staticmethod
    def filter_prs_by_keywords(prs: list, keywords: list[str]) -> list:
        """Filter pull requests by keywords in their titles.

        Args:
            prs: List of pull requests to filter
            keywords: List of keywords to search for in titles (case-insensitive)

        Returns:
            Filtered list of pull requests
        """
        return [pr for pr in prs if any(kw in pr.title.lower() for kw in keywords)]

    @staticmethod
    def categorize_prs_by_keywords(prs: list, keyword_groups: dict[str, list[str]]) -> dict[str, list]:
        """Categorize pull requests by multiple keyword groups in a single pass.

        This is more efficient than calling filter_prs_by_keywords multiple times
        as it only iterates through the PRs once.

        Args:
            prs: List of pull requests to categorize
            keyword_groups: Dictionary mapping category names to keyword lists
                Example: {'doc': ['doc', 'readme'], 'test': ['test']}

        Returns:
            Dictionary mapping category names to filtered PR lists
        """
        # Initialize result dictionary with empty lists
        result = {category: [] for category in keyword_groups}

        # Single pass through all PRs
        for pr in prs:
            pr_title_lower = pr.title.lower()
            for category, keywords in keyword_groups.items():
                if any(kw in pr_title_lower for kw in keywords):
                    result[category].append(pr)

        return result

    @staticmethod
    def extract_keyword_based_insight(
        prs: list,
        keywords: list[str],
        threshold: int,
        message_template: str
    ) -> Optional[str]:
        """Extract insight based on keyword filtering and threshold check.

        Args:
            prs: List of pull requests
            keywords: Keywords to filter by
            threshold: Minimum count for insight
            message_template: Template for the insight message (with {count} placeholder)

        Returns:
            Formatted message if threshold exceeded, None otherwise
        """
        if not prs:
            return None

        filtered_prs = InsightExtractor.filter_prs_by_keywords(prs, keywords)
        if len(filtered_prs) > threshold:
            return message_template.format(count=len(filtered_prs))
        return None
