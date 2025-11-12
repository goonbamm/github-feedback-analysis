"""Review collection operations."""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional

import requests

from .base_collector import BaseCollector
from .console import Console
from .models import AnalysisFilters

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
            if not self._pr_matches_file_filters(repo, pr, filters, pr_file_cache):
                continue
            valid_prs.append(pr)

        # Parallelize review fetching
        def fetch_pr_reviews(pr: Dict[str, Any]) -> int:
            number = pr["number"]
            count = 0

            # Fetch all reviews for this PR using paginate
            all_reviews = self.api_client.paginate(
                f"repos/{repo}/pulls/{number}/reviews",
                base_params={"per_page": 100},
                per_page=100,
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
                if self.filter_bot(author, filters):
                    continue
                count += 1

            return count

        total = 0
        completed_count = 0
        total_prs = len(valid_prs)

        with ThreadPoolExecutor(max_workers=5) as executor:
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

        # Get pull requests first
        # If author is specified, use Issues API for efficient filtering
        if author:
            params: Dict[str, Any] = {
                "creator": author,
                "state": "all",
                "sort": "created",
                "direction": "desc",
                "per_page": 50,
            }
            prs = self.api_client.request_list(f"repos/{repo}/issues", params)
        else:
            params: Dict[str, Any] = {
                "state": "all",
                "sort": "created",
                "direction": "desc",
                "per_page": 50,
            }
            prs = self.api_client.request_list(f"repos/{repo}/pulls", params)
        for pr in prs:
            # Skip non-PRs when using Issues API
            if author and "pull_request" not in pr:
                continue

            if len(review_comments) >= limit:
                break

            created_at_raw = pr.get("created_at")
            if not created_at_raw:
                continue

            created_at = self.parse_timestamp(created_at_raw).astimezone(timezone.utc)
            if created_at < since:
                continue

            number = pr.get("number")
            if not number:
                continue

            # Get reviews for this PR
            try:
                reviews = self.api_client.request_list(
                    f"repos/{repo}/pulls/{number}/reviews",
                    {"per_page": 100},
                )

                for review in reviews:
                    if len(review_comments) >= limit:
                        break

                    body = review.get("body", "").strip()
                    if not body:
                        continue

                    review_author = review.get("user")
                    if self.filter_bot(review_author, filters):
                        continue

                    review_comments.append(
                        {
                            "pr_number": number,
                            "author": (review.get("user") or {}).get("login", ""),
                            "body": body,
                            "state": review.get("state", ""),
                            "submitted_at": review.get("submitted_at", ""),
                        }
                    )
            except (requests.HTTPError, ValueError) as exc:
                # Skip PRs that fail to fetch reviews
                logger.warning(f"Failed to fetch reviews for PR #{number}: {exc}")
                continue

        return review_comments[:limit]

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

    def _pr_matches_file_filters(
        self,
        repo: str,
        pr: Dict[str, Any],
        filters: AnalysisFilters,
        cache: Dict[int, List[Dict[str, Any]]],
    ) -> bool:
        """Check if PR matches file filters (reused from PR collector logic).

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
                f"repos/{repo}/pulls/{number}/files", {"per_page": 100}
            )
            cache[number] = files

        filenames = [entry.get("filename", "") for entry in files]
        return self.apply_file_filters(filenames, filters)
