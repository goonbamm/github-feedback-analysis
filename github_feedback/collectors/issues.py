"""Issue collection operations."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from ..api.params import build_list_params
from .base import BaseCollector
from ..filters import FilterHelper
from ..core.models import AnalysisFilters


class IssueCollector(BaseCollector):
    """Collector specialized for issue operations."""

    def count_issues(self, repo: str, since: datetime, filters: AnalysisFilters, author: Optional[str] = None) -> int:
        """Count issues matching filters.

        Args:
            repo: Repository name (owner/repo)
            since: Start date for issue collection
            filters: Analysis filters to apply
            author: Optional GitHub username to filter issues by creator

        Returns:
            Number of issues matching filters
        """
        params = build_list_params(since=since.isoformat())
        if author:
            params["creator"] = author

        all_issues = self.api_client.paginate(
            f"repos/{repo}/issues", base_params=params
        )

        # Count issues that pass filters
        total = 0
        for issue in all_issues:
            if "pull_request" in issue:
                continue
            author = issue.get("user")
            if self.filter_helper.filter_bot(author, filters):
                continue
            if not self._issue_matches_filters(issue, filters):
                continue
            total += 1

        return total

    def collect_issue_details(
        self,
        repo: str,
        since: datetime,
        filters: Optional[AnalysisFilters] = None,
        limit: int = 100,
        author: Optional[str] = None,
    ) -> List[Dict[str, str]]:
        """Collect issue details for quality analysis.

        Args:
            repo: Repository name (owner/repo)
            since: Start date for issue collection
            filters: Optional analysis filters
            limit: Maximum number of issues to collect
            author: Optional GitHub username to filter issues by creator

        Returns:
            List of issue detail dictionaries
        """
        filters = filters or AnalysisFilters()
        issues: List[Dict[str, str]] = []

        params: Dict[str, Any] = {
            "state": "all",
            "sort": "created",
            "direction": "desc",
            "per_page": limit,
            "since": since.isoformat(),
        }
        if author:
            params["creator"] = author

        data = self.api_client.request_list(f"repos/{repo}/issues", params)
        for issue in data:
            # Skip pull requests (GitHub API returns them as issues)
            if "pull_request" in issue:
                continue

            author = issue.get("user")
            if self.filter_helper.filter_bot(author, filters):
                continue

            issues.append(
                {
                    "number": issue.get("number", 0),
                    "title": issue.get("title", ""),
                    "body": issue.get("body", "") or "",
                    "author": (issue.get("user") or {}).get("login", ""),
                    "url": issue.get("html_url", ""),
                    "state": issue.get("state", ""),
                    "created_at": issue.get("created_at", ""),
                }
            )

            if len(issues) >= limit:
                break

        return issues[:limit]

    def _issue_matches_filters(
        self, issue: Dict[str, Any], filters: AnalysisFilters
    ) -> bool:
        """Check if issue matches filters.

        Args:
            issue: GitHub issue object
            filters: Analysis filters

        Returns:
            True if issue matches filters
        """
        filenames = FilterHelper.extract_issue_files(issue)
        return self.apply_file_filters(filenames, filters)
