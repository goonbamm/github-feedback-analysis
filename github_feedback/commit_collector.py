"""Commit collection operations."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Sequence, Set

from .base_collector import BaseCollector
from .models import AnalysisFilters

logger = logging.getLogger(__name__)


class CommitCollector(BaseCollector):
    """Collector specialized for commit-related operations."""

    def count_commits(
        self, repo: str, since: datetime, filters: AnalysisFilters, author: Optional[str] = None
    ) -> int:
        """Count commits matching filters.

        Args:
            repo: Repository name (owner/repo)
            since: Start date for commit collection
            filters: Analysis filters to apply
            author: Optional GitHub username to filter commits by author

        Returns:
            Number of commits matching filters
        """
        total = 0
        seen_shas: Set[str] = set()
        include_branches = self._get_branches_to_process(repo, filters)

        if not include_branches:
            return 0

        path_filters = filters.include_paths or [None]
        commit_file_cache: Dict[str, List[str]] = {}

        for branch in include_branches:
            for path_filter in path_filters:
                page = 1
                base_params: Dict[str, Any] = {
                    "since": since.isoformat(),
                    "per_page": 100,
                }
                if branch:
                    base_params["sha"] = branch
                if path_filter:
                    base_params["path"] = path_filter
                if author:
                    base_params["author"] = author

                while True:
                    page_params = base_params | {"page": page}
                    data = self.api_client.request_list(
                        f"repos/{repo}/commits", page_params
                    )
                    if not data:
                        break

                    for commit in data:
                        author = commit.get("author")
                        if self.filter_bot(author, filters):
                            continue
                        sha = commit.get("sha")
                        if not sha or sha in seen_shas:
                            continue
                        if not self._commit_matches_path_filters(
                            repo, sha, filters, commit_file_cache
                        ):
                            continue
                        seen_shas.add(sha)
                        total += 1

                    if len(data) < 100:
                        break
                    page += 1

        return total

    def collect_commit_messages(
        self,
        repo: str,
        since: datetime,
        filters: Optional[AnalysisFilters] = None,
        limit: int = 100,
        author: Optional[str] = None,
    ) -> List[Dict[str, str]]:
        """Collect commit messages for quality analysis.

        Args:
            repo: Repository name (owner/repo)
            since: Start date for commit collection
            filters: Optional analysis filters
            limit: Maximum number of commits to collect
            author: Optional GitHub username to filter commits by author

        Returns:
            List of commit message dictionaries
        """
        filters = filters or AnalysisFilters()
        commits: List[Dict[str, str]] = []
        seen_shas: Set[str] = set()
        include_branches = self._get_branches_to_process(repo, filters)

        if not include_branches:
            return []

        for branch in include_branches:
            if len(commits) >= limit:
                break

            params: Dict[str, Any] = {
                "since": since.isoformat(),
                "per_page": min(100, limit - len(commits)),
            }
            if branch:
                params["sha"] = branch
            if author:
                params["author"] = author

            data = self.api_client.request_list(f"repos/{repo}/commits", params)
            for item in data:
                sha = item.get("sha", "")
                if sha in seen_shas:
                    continue
                seen_shas.add(sha)

                author = item.get("author")
                if self.filter_bot(author, filters):
                    continue

                commit_data = item.get("commit", {})
                message = commit_data.get("message", "")
                commits.append(
                    {
                        "sha": sha,
                        "message": message,
                        "author": (commit_data.get("author") or {}).get("name", ""),
                        "date": commit_data.get("author", {}).get("date", ""),
                    }
                )

                if len(commits) >= limit:
                    break

        return commits[:limit]

    def _get_branches_to_process(
        self, repo: str, filters: AnalysisFilters
    ) -> Sequence[Optional[str]]:
        """Determine which branches to process based on filters.

        Args:
            repo: Repository name (owner/repo)
            filters: Analysis filters

        Returns:
            List of branch names to process (None means default branch)
        """
        include_branches: Sequence[Optional[str]]
        exclude_branches = set(filters.exclude_branches)

        if filters.include_branches:
            include_branches = [
                branch
                for branch in filters.include_branches
                if branch not in exclude_branches
            ]
        elif exclude_branches:
            branches = self.api_client.request_all(
                f"repos/{repo}/branches",
                {"per_page": 100},
            )
            include_branches = [
                branch.get("name")
                for branch in branches
                if branch.get("name") and branch.get("name") not in exclude_branches
            ]
        else:
            include_branches = [None]

        return include_branches

    def _commit_matches_path_filters(
        self,
        repo: str,
        sha: str,
        filters: AnalysisFilters,
        cache: Dict[str, List[str]],
    ) -> bool:
        """Check if commit matches path filters.

        Args:
            repo: Repository name
            sha: Commit SHA
            filters: Analysis filters
            cache: File cache to avoid redundant API calls

        Returns:
            True if commit matches filters
        """
        # Get files from cache or fetch from API
        files = cache.get(sha)
        if files is None:
            payload = self.api_client.request_json(f"repos/{repo}/commits/{sha}")
            file_entries = payload.get("files") or []
            files = [entry.get("filename", "") for entry in file_entries]
            cache[sha] = files

        return self.apply_file_filters(files, filters)
