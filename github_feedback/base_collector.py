"""Base collector with common functionality."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

from .api_client import GitHubApiClient
from .config import Config
from .filters import FilterHelper
from .models import AnalysisFilters


class BaseCollector:
    """Base class for all collectors with common utilities."""

    def __init__(self, config: Config, api_client: GitHubApiClient):
        """Initialize base collector.

        Args:
            config: Configuration object
            api_client: GitHub API client instance
        """
        self.config = config
        self.api_client = api_client
        self.filter_helper = FilterHelper()

    @staticmethod
    def parse_timestamp(value: str) -> datetime:
        """Parse GitHub API timestamp string.

        Args:
            value: ISO format timestamp string

        Returns:
            Parsed datetime object
        """
        if value.endswith("Z"):
            value = value.replace("Z", "+00:00")
        return datetime.fromisoformat(value)

    def filter_bot(self, author: Any, filters: AnalysisFilters) -> bool:
        """Check if author should be filtered as a bot.

        Args:
            author: GitHub author object
            filters: Analysis filters

        Returns:
            True if author is a bot and should be filtered
        """
        return self.filter_helper.filter_bot(author, filters)

    def apply_file_filters(self, filenames: list[str], filters: AnalysisFilters) -> bool:
        """Apply file filters to filename list.

        Args:
            filenames: List of file paths
            filters: Analysis filters

        Returns:
            True if files pass filters
        """
        return self.filter_helper.apply_file_filters(filenames, filters)

    def pr_matches_branch_filters(
        self, pr: Dict[str, Any], filters: AnalysisFilters
    ) -> bool:
        """Check if PR matches branch filters.

        Args:
            pr: Pull request object
            filters: Analysis filters

        Returns:
            True if PR passes branch filters
        """
        return self.filter_helper.pr_matches_branch_filters(pr, filters)
