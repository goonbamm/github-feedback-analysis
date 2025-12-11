"""Base collector with common functionality."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List

from ..api.client import GitHubApiClient
from ..api.params import build_pagination_params
from ..core.config import Config
from ..filters import FilterHelper
from ..core.models import AnalysisFilters


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

    def pr_matches_file_filters(
        self,
        repo: str,
        pr: Dict[str, Any],
        filters: AnalysisFilters,
        cache: Dict[int, List[Dict[str, Any]]],
    ) -> bool:
        """Check if PR matches file filters.

        Args:
            repo: Repository name
            pr: Pull request object
            filters: Analysis filters
            cache: File cache to avoid redundant API calls

        Returns:
            True if PR matches filters
        """
        # Early exit if no file filters are specified
        if not (
            filters.include_paths
            or filters.exclude_paths
            or filters.include_languages
        ):
            return True

        # Get PR files from cache or fetch from API
        number = int(pr.get("number", 0))
        files = cache.get(number)
        if files is None:
            files = self.api_client.request_all(
                f"repos/{repo}/pulls/{number}/files", build_pagination_params()
            )
            cache[number] = files

        filenames = [entry.get("filename", "") for entry in files]
        return self.apply_file_filters(filenames, filters)
