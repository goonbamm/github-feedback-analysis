"""Commit collection operations."""

from __future__ import annotations

import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Any, Dict, List, Optional, Sequence, Set

from .api_params import build_commits_params, build_pagination_params
from .base_collector import BaseCollector
from .constants import THREAD_POOL_CONFIG
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
        include_branches = self._get_branches_to_process(repo, filters)

        if not include_branches:
            return 0

        # Check if we need file filtering
        has_file_filters = bool(
            filters.include_paths
            or filters.exclude_paths
            or filters.include_languages
        )

        # Use shared cache across all branches to avoid duplicate fetches
        commit_file_cache: Dict[str, List[str]] = {}
        seen_shas: Set[str] = set()

        # Process branches in parallel for better performance
        def count_commits_for_branch(branch: Optional[str]) -> tuple[int, Set[str], Dict[str, List[str]]]:
            """Count commits for a single branch."""
            local_count = 0
            local_shas: Set[str] = set()
            local_cache: Dict[str, List[str]] = {}

            path_filters = filters.include_paths or [None]

            for path_filter in path_filters:
                base_params = build_commits_params(
                    sha=branch,
                    path=path_filter,
                    since=since.isoformat(),
                    author=author,
                )

                # Use paginate helper for cleaner code
                commits_data = self.api_client.paginate(
                    f"repos/{repo}/commits",
                    base_params=base_params,
                )

                for commit in commits_data:
                    commit_author = commit.get("author")
                    if self.filter_bot(commit_author, filters):
                        continue

                    sha = commit.get("sha")
                    if not sha or sha in local_shas:
                        continue

                    # Only check file filters if needed
                    if has_file_filters:
                        if not self._commit_matches_path_filters(
                            repo, sha, filters, local_cache
                        ):
                            continue

                    local_shas.add(sha)
                    local_count += 1

            return local_count, local_shas, local_cache

        # For single branch, no need for parallelization overhead
        if len(include_branches) == 1:
            total, seen_shas, commit_file_cache = count_commits_for_branch(include_branches[0])
            return total

        # Parallel processing for multiple branches
        total = 0
        max_workers = min(
            THREAD_POOL_CONFIG['max_workers_commit_branches'],
            len(include_branches)
        )
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(count_commits_for_branch, branch): branch
                for branch in include_branches
            }

            for future in as_completed(futures):
                branch = futures[future]
                try:
                    count, shas, cache = future.result()
                    # Merge results, avoiding duplicates
                    for sha in shas:
                        if sha not in seen_shas:
                            seen_shas.add(sha)
                            total += 1
                    # Merge cache
                    commit_file_cache.update(cache)
                except (requests.RequestException, ValueError, KeyError, json.JSONDecodeError) as exc:
                    logger.warning(f"Failed to count commits for branch {branch}: {exc}")

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
                build_pagination_params(),
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
