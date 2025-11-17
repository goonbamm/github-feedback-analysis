"""Analytics and statistics collection operations."""

from __future__ import annotations

import logging
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Any, Dict, List, Optional, Sequence, Set

import requests

from .api_params import build_commits_params, build_list_params, build_pagination_params
from .base_collector import BaseCollector
from .console import Console
from .constants import THREAD_POOL_CONFIG
from .filters import FilterHelper
from .models import AnalysisFilters

logger = logging.getLogger(__name__)
console = Console()


class AnalyticsCollector(BaseCollector):
    """Collector specialized for analytics and statistics."""

    def collect_monthly_trends(
        self,
        repo: str,
        since: datetime,
        filters: Optional[AnalysisFilters] = None,
    ) -> List[Dict[str, Any]]:
        """Collect monthly activity trends for time-series analysis.

        Args:
            repo: Repository name (owner/repo)
            since: Start date for trend collection
            filters: Optional analysis filters

        Returns:
            List of monthly trend dictionaries
        """
        filters = filters or AnalysisFilters()

        # Initialize monthly buckets
        monthly_data: Dict[str, Dict[str, int]] = defaultdict(
            lambda: {"commits": 0, "pull_requests": 0, "reviews": 0, "issues": 0}
        )

        # Collect commits by month
        seen_shas: Set[str] = set()
        include_branches: Sequence[Optional[str]] = [None]

        for branch in include_branches:
            params = build_commits_params(
                sha=branch,
                since=since.isoformat(),
            )

            try:
                commits = self.api_client.request_all(f"repos/{repo}/commits", params)
                for commit in commits:
                    sha = commit.get("sha", "")
                    if sha in seen_shas:
                        continue
                    seen_shas.add(sha)

                    author = commit.get("author")
                    if self.filter_helper.filter_bot(author, filters):
                        continue

                    commit_data = commit.get("commit", {})
                    date_str = commit_data.get("author", {}).get("date", "")
                    if date_str:
                        commit_date = self.parse_timestamp(date_str)
                        month_key = commit_date.strftime("%Y-%m")
                        monthly_data[month_key]["commits"] += 1
            except (requests.HTTPError, ValueError) as exc:
                logger.warning(f"Failed to collect commits for monthly trends: {exc}")

        # Collect PRs by month
        try:
            params = build_list_params()
            prs = self.api_client.request_all(f"repos/{repo}/pulls", params)
            for pr in prs:
                created_at_raw = pr.get("created_at")
                if not created_at_raw:
                    continue

                created_at = self.parse_timestamp(created_at_raw).astimezone()
                if created_at < since:
                    continue

                author = pr.get("user")
                if self.filter_helper.filter_bot(author, filters):
                    continue

                month_key = created_at.strftime("%Y-%m")
                monthly_data[month_key]["pull_requests"] += 1
        except (requests.HTTPError, ValueError) as exc:
            logger.warning(f"Failed to collect PRs for monthly trends: {exc}")

        # Convert to list and sort by month
        result = []
        for month_key in sorted(monthly_data.keys()):
            result.append({"month": month_key, **monthly_data[month_key]})

        return result

    def collect_tech_stack(
        self,
        repo: str,
        pr_metadata: List[Dict[str, Any]],
    ) -> Dict[str, int]:
        """Analyze technology stack from PR file changes.

        Args:
            repo: Repository name (owner/repo)
            pr_metadata: List of PR metadata

        Returns:
            Dictionary mapping language names to counts
        """
        language_counts: Dict[str, int] = {}

        def fetch_pr_files(pr: Dict[str, Any]) -> Dict[str, int]:
            """Fetch files for a single PR and count languages."""
            number = int(pr.get("number", 0))
            local_counts: Dict[str, int] = {}

            try:
                files = self.api_client.request_all(
                    f"repos/{repo}/pulls/{number}/files", build_pagination_params()
                )

                for file_entry in files:
                    filename = file_entry.get("filename", "")
                    language = FilterHelper.filename_to_language(filename)
                    if language:
                        local_counts[language] = local_counts.get(language, 0) + 1

            except (requests.HTTPError, ValueError) as exc:
                logger.warning(f"Failed to fetch files for PR #{number}: {exc}")

            return local_counts

        # Parallelize file fetching for recent PRs
        from .constants import COLLECTION_LIMITS
        max_prs = COLLECTION_LIMITS['max_prs_to_process']
        prs_to_process = pr_metadata[:max_prs]
        completed_count = 0
        total_prs = len(prs_to_process)

        max_workers = THREAD_POOL_CONFIG['max_workers_pr_fetch']
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(fetch_pr_files, pr): pr for pr in prs_to_process
            }

            for future in as_completed(futures):
                completed_count += 1
                try:
                    local_counts = future.result()
                    for language, count in local_counts.items():
                        language_counts[language] = (
                            language_counts.get(language, 0) + count
                        )
                    if completed_count % 10 == 0 or completed_count == total_prs:
                        console.log(
                            f"Tech stack analysis progress: {completed_count}/{total_prs} PRs analyzed"
                        )
                except Exception as exc:
                    logger.warning(f"Failed to process PR for tech stack analysis: {exc}")
                    continue

        return language_counts

    def collect_collaboration_network(
        self,
        repo: str,
        pr_metadata: List[Dict[str, Any]],
        filters: Optional[AnalysisFilters] = None,
        author: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Analyze collaboration patterns from PR reviews.

        Args:
            repo: Repository name (owner/repo)
            pr_metadata: List of PR metadata
            filters: Optional analysis filters
            author: Optional GitHub username to exclude from collaborators (self)

        Returns:
            Dictionary with collaboration metrics
        """
        filters = filters or AnalysisFilters()
        reviewer_counts: Dict[str, int] = {}
        total_reviews_received = 0
        unique_reviewers: Set[str] = set()

        def fetch_pr_reviews(
            pr: Dict[str, Any]
        ) -> tuple[Dict[str, int], Set[str], int]:
            """Fetch reviews for a single PR and count reviewers."""
            number = pr["number"]
            local_counts: Dict[str, int] = {}
            local_reviewers: Set[str] = set()
            local_total = 0

            try:
                reviews = self.api_client.request_all(
                    f"repos/{repo}/pulls/{number}/reviews", build_pagination_params()
                )

                for review in reviews:
                    reviewer = review.get("user")
                    if self.filter_helper.filter_bot(reviewer, filters):
                        continue

                    reviewer_login = (reviewer or {}).get("login", "")
                    if not reviewer_login:
                        continue

                    # Exclude the author from collaborators (self-reviews)
                    if author and reviewer_login == author:
                        continue

                    local_counts[reviewer_login] = (
                        local_counts.get(reviewer_login, 0) + 1
                    )
                    local_reviewers.add(reviewer_login)
                    local_total += 1
            except (requests.HTTPError, ValueError) as exc:
                logger.warning(f"Failed to fetch reviews for PR #{number}: {exc}")

            return local_counts, local_reviewers, local_total

        # Parallelize review fetching for recent 100 PRs
        prs_to_process = pr_metadata[:100]
        completed_count = 0
        total_prs = len(prs_to_process)

        max_workers = THREAD_POOL_CONFIG['max_workers_pr_fetch']
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(fetch_pr_reviews, pr): pr for pr in prs_to_process
            }

            for future in as_completed(futures):
                completed_count += 1
                try:
                    local_counts, local_reviewers, local_total = future.result()
                    for reviewer, count in local_counts.items():
                        reviewer_counts[reviewer] = (
                            reviewer_counts.get(reviewer, 0) + count
                        )
                    unique_reviewers.update(local_reviewers)
                    total_reviews_received += local_total
                    if completed_count % 20 == 0 or completed_count == total_prs:
                        console.log(
                            f"Collaboration network progress: {completed_count}/{total_prs} PRs analyzed"
                        )
                except Exception as exc:
                    logger.warning(f"Failed to process PR for collaboration network: {exc}")
                    continue

        return {
            "pr_reviewers": reviewer_counts,
            "review_received_count": total_reviews_received,
            "unique_collaborators": len(unique_reviewers),
        }
