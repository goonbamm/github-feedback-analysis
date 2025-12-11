"""Review collection operations."""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional

import requests

from .api_params import build_pagination_params
from .base_collector import BaseCollector
from ..core.console import Console
from ..core.constants import THREAD_POOL_CONFIG
from ..core.models import AnalysisFilters

logger = logging.getLogger(__name__)
console = Console()


class ReviewCollector(BaseCollector):
    """Collector specialized for review operations."""

    def count_reviews(
        self,
        repo: str,
        pull_requests: Iterable[Dict[str, Any]],
        since: datetime,
        filters: AnalysisFilters,
    ) -> int:
        """Count reviews matching filters.

        Args:
            repo: Repository name (owner/repo)
            pull_requests: Iterable of PR metadata
            since: Start date for review collection
            filters: Analysis filters to apply

        Returns:
            Number of reviews matching filters
        """
        pr_file_cache: Dict[int, List[Dict[str, Any]]] = {}
        valid_prs = []

        # Filter PRs first
        for pr in pull_requests:
            if not self.pr_matches_branch_filters(pr, filters):
                continue
            if not self.pr_matches_file_filters(repo, pr, filters, pr_file_cache):
                continue
            valid_prs.append(pr)

        # Parallelize review fetching
        def fetch_pr_reviews(pr: Dict[str, Any]) -> int:
            number = pr["number"]
            count = 0

            # Fetch all reviews for this PR using paginate
            all_reviews = self.api_client.paginate(
                f"repos/{repo}/pulls/{number}/reviews",
                base_params=build_pagination_params(),
            )

            # Count reviews that pass filters
            for review in all_reviews:
                submitted_at = review.get("submitted_at")
                if submitted_at:
                    submitted_dt = self.parse_timestamp(submitted_at).astimezone(
                        timezone.utc
                    )
                    if submitted_dt < since:
                        continue
                author = review.get("user")
                if self.filter_helper.filter_bot(author, filters):
                    continue
                count += 1

            return count

        total = 0
        completed_count = 0
        total_prs = len(valid_prs)

        max_workers = THREAD_POOL_CONFIG['max_workers_pr_fetch']
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(fetch_pr_reviews, pr): pr for pr in valid_prs}
            for future in as_completed(futures):
                completed_count += 1
                pr_num = futures[future]
                try:
                    count = future.result()
                    total += count
                    if completed_count % 10 == 0 or completed_count == total_prs:
                        console.log(
                            f"Review counting progress: {completed_count}/{total_prs} PRs processed"
                        )
                except requests.HTTPError as exc:
                    logger.warning(
                        f"Failed to fetch reviews for PR #{pr_num}: "
                        f"HTTP {exc.response.status_code if exc.response else 'error'}"
                    )
                except Exception as exc:
                    logger.warning(f"Failed to fetch reviews for PR #{pr_num}: {exc}")

        return total

    def collect_review_comments_detailed(
        self,
        repo: str,
        since: datetime,
        filters: Optional[AnalysisFilters] = None,
        limit: int = 100,
        author: Optional[str] = None,
    ) -> List[Dict[str, str]]:
        """Collect review comments for tone analysis.

        Args:
            repo: Repository name (owner/repo)
            since: Start date for review collection
            filters: Optional analysis filters
            limit: Maximum number of comments to collect
            author: Optional GitHub username to filter PRs by author

        Returns:
            List of review comment dictionaries
        """
        filters = filters or AnalysisFilters()
        review_comments: List[Dict[str, str]] = []

        params: Dict[str, Any] = {
            "state": "all",
            "sort": "created",
            "direction": "desc",
            "per_page": 50,
        }
        endpoint = f"repos/{repo}/pulls"
        if author:
            params["creator"] = author
            endpoint = f"repos/{repo}/issues"

        def should_stop(pr: Dict[str, Any]) -> bool:
            created_at_raw = pr.get("created_at")
            if not created_at_raw:
                return False
            created_at = self.parse_timestamp(created_at_raw).astimezone(timezone.utc)
            return created_at < since

        pull_requests = self.api_client.paginate(
            endpoint,
            base_params=params,
            per_page=50,
            early_stop=should_stop,
        )

        for pr in pull_requests:
            if len(review_comments) >= limit:
                break

            # Skip non-PRs when using Issues API
            if author and "pull_request" not in pr:
                continue

            created_at_raw = pr.get("created_at")
            if not created_at_raw:
                continue

            created_at = self.parse_timestamp(created_at_raw).astimezone(timezone.utc)
            if created_at < since:
                continue

            number = pr.get("number")
            if not number:
                continue

            comments = self._fetch_review_comments_for_pr(repo, number, filters)
            for comment in comments:
                review_comments.append(comment)
                if len(review_comments) >= limit:
                    break

        return review_comments[:limit]

    def _fetch_review_comments_for_pr(
        self,
        repo: str,
        pr_number: int,
        filters: AnalysisFilters,
    ) -> List[Dict[str, str]]:
        """Fetch and filter review comments for a single PR."""

        try:
            reviews = self.api_client.paginate(
                f"repos/{repo}/pulls/{pr_number}/reviews",
                base_params=build_pagination_params(),
            )
        except (requests.HTTPError, ValueError) as exc:
            logger.warning(f"Failed to fetch reviews for PR #{pr_number}: {exc}")
            return []

        comments: List[Dict[str, str]] = []
        for review in reviews:
            body = review.get("body", "").strip()
            if not body:
                continue

            review_author = review.get("user")
            if self.filter_helper.filter_bot(review_author, filters):
                continue

            comments.append(
                {
                    "pr_number": pr_number,
                    "author": (review_author or {}).get("login", ""),
                    "body": body,
                    "state": review.get("state", ""),
                    "submitted_at": review.get("submitted_at", ""),
                    "url": review.get("html_url", ""),
                }
            )

        return comments

    def get_authenticated_user(self) -> str:
        """Return the username of the authenticated user (PAT owner).

        Returns:
            Username string

        Raises:
            ValueError: If username cannot be retrieved
        """
        user_data = self.api_client.request_json("user")
        username = user_data.get("login", "")
        if not username:
            raise ValueError("Failed to retrieve authenticated user from PAT")
        return username
