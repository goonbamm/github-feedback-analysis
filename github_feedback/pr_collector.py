"""Pull request collection operations."""

from __future__ import annotations

import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Set

import requests

from .api_params import build_list_params, build_pagination_params
from .base_collector import BaseCollector
from .constants import THREAD_POOL_CONFIG
from .models import (
    AnalysisFilters,
    PullRequestFile,
    PullRequestReviewBundle,
    PullRequestSummary,
)

logger = logging.getLogger(__name__)


class PullRequestCollector(BaseCollector):
    """Collector specialized for pull request operations."""

    def list_pull_requests(
        self, repo: str, since: datetime, filters: AnalysisFilters, author: Optional[str] = None
    ) -> tuple[int, List[Dict[str, Any]]]:
        """List pull requests matching filters.

        Args:
            repo: Repository name (owner/repo)
            since: Start date for PR collection
            filters: Analysis filters to apply
            author: Optional GitHub username to filter PRs by author

        Returns:
            Tuple of (count, metadata list)
        """
        # Ensure since is timezone-aware for comparison
        if since.tzinfo is None:
            since = since.replace(tzinfo=timezone.utc)

        # If author is specified, use Issues API for efficient filtering
        if author:
            return self._list_pull_requests_by_author(repo, since, filters, author)

        params = build_list_params()

        def should_stop(pr: Dict[str, Any]) -> bool:
            """Early stop condition: PR created before analysis period."""
            created_at = self.parse_timestamp(pr["created_at"]).astimezone(timezone.utc)
            return created_at < since

        all_prs = self.api_client.paginate(
            f"repos/{repo}/pulls",
            base_params=params,
            per_page=100,
            early_stop=should_stop,
        )

        metadata = self._apply_pr_filters(repo, all_prs, filters)
        return len(metadata), metadata

    def _list_pull_requests_by_author(
        self, repo: str, since: datetime, filters: AnalysisFilters, author: str
    ) -> tuple[int, List[Dict[str, Any]]]:
        """List pull requests by specific author using Issues API.

        Args:
            repo: Repository name (owner/repo)
            since: Start date for PR collection
            filters: Analysis filters to apply
            author: GitHub username to filter PRs by

        Returns:
            Tuple of (count, metadata list)
        """
        # Ensure since is timezone-aware for comparison
        if since.tzinfo is None:
            since = since.replace(tzinfo=timezone.utc)

        # Use Issues API with creator filter
        params = build_list_params(creator=author)

        all_issues = self.api_client.paginate(
            f"repos/{repo}/issues", base_params=params
        )

        # Filter issues for PRs and date range
        pr_numbers_to_fetch = []
        for issue in all_issues:
            # Skip non-PRs
            if "pull_request" not in issue:
                continue

            # Check date filter
            created_at_raw = issue.get("created_at")
            if created_at_raw:
                created_at = self.parse_timestamp(created_at_raw).astimezone(timezone.utc)
                if created_at < since:
                    continue

            pr_number = issue.get("number")
            if pr_number:
                pr_numbers_to_fetch.append(pr_number)

        # Fetch full PR data in parallel (solving N+1 query problem)
        def fetch_pr_data(pr_number: int) -> Optional[Dict[str, Any]]:
            """Fetch PR data with error handling."""
            try:
                return self.api_client.request_json(f"repos/{repo}/pulls/{pr_number}")
            except (requests.RequestException, ValueError, KeyError, json.JSONDecodeError) as exc:
                logger.warning(f"Failed to fetch PR #{pr_number}: {exc}")
                return None

        # Parallel fetch of PR details
        prs_raw: List[Dict[str, Any]] = []
        max_workers = THREAD_POOL_CONFIG['max_workers_pr_fetch']
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_pr = {
                executor.submit(fetch_pr_data, pr_num): pr_num
                for pr_num in pr_numbers_to_fetch
            }

            for future in as_completed(future_to_pr):
                pr_data = future.result()
                if pr_data:
                    prs_raw.append(pr_data)

        metadata = self._apply_pr_filters(repo, prs_raw, filters)
        return len(metadata), metadata

    def _apply_pr_filters(
        self,
        repo: str,
        pull_requests: Iterable[Dict[str, Any]],
        filters: AnalysisFilters,
    ) -> List[Dict[str, Any]]:
        """Apply all PR filters consistently across listing strategies."""

        pr_file_cache: Dict[int, List[Dict[str, Any]]] = {}
        metadata: List[Dict[str, Any]] = []

        for pr in pull_requests:
            author = pr.get("user")
            if self.filter_helper.filter_bot(author, filters):
                continue
            if not self.pr_matches_branch_filters(pr, filters):
                continue
            if not self.pr_matches_file_filters(repo, pr, filters, pr_file_cache):
                continue
            metadata.append(pr)

        return metadata

    def build_pull_request_examples(
        self, pr_metadata: List[Dict[str, Any]]
    ) -> List[PullRequestSummary]:
        """Transform raw PR metadata into reporting examples.

        Args:
            pr_metadata: List of raw PR metadata from API

        Returns:
            List of PullRequestSummary objects
        """
        examples: List[PullRequestSummary] = []
        for pr in pr_metadata[:5]:
            author = pr.get("user") or {}
            merged_at_raw = pr.get("merged_at")
            merged_at = (
                self.parse_timestamp(merged_at_raw).astimezone(timezone.utc)
                if merged_at_raw
                else None
            )
            created_at = self.parse_timestamp(pr["created_at"]).astimezone(timezone.utc)
            examples.append(
                PullRequestSummary(
                    number=int(pr.get("number", 0)),
                    title=(pr.get("title") or "(no title)").strip(),
                    author=author.get("login", "unknown"),
                    html_url=pr.get("html_url", ""),
                    created_at=created_at,
                    merged_at=merged_at,
                    additions=int(pr.get("additions") or 0),
                    deletions=int(pr.get("deletions") or 0),
                )
            )
        return examples

    def collect_pr_titles(
        self,
        repo: str,
        since: datetime,
        filters: Optional[AnalysisFilters] = None,
        limit: int = 100,
        author: Optional[str] = None,
    ) -> List[Dict[str, str]]:
        """Collect PR titles for quality analysis.

        Args:
            repo: Repository name (owner/repo)
            since: Start date for PR collection
            filters: Optional analysis filters
            limit: Maximum number of PRs to collect
            author: Optional GitHub username to filter PRs by author

        Returns:
            List of PR title dictionaries
        """
        # Ensure since is timezone-aware for comparison
        if since.tzinfo is None:
            since = since.replace(tzinfo=timezone.utc)

        filters = filters or AnalysisFilters()
        pr_titles: List[Dict[str, str]] = []

        # If author is specified, use Issues API for efficient filtering
        if author:
            params: Dict[str, Any] = {
                "creator": author,
                "state": "all",
                "sort": "created",
                "direction": "desc",
                "per_page": limit,
            }
            # Use Issues API which supports creator filter
            data = self.api_client.request_list(f"repos/{repo}/issues", params)
        else:
            params: Dict[str, Any] = {
                "state": "all",
                "sort": "created",
                "direction": "desc",
                "per_page": limit,
            }
            data = self.api_client.request_list(f"repos/{repo}/pulls", params)
        for item in data:
            # Skip non-PRs when using Issues API
            if author and "pull_request" not in item:
                continue

            created_at_raw = item.get("created_at")
            if not created_at_raw:
                continue

            created_at = self.parse_timestamp(created_at_raw).astimezone(timezone.utc)
            if created_at < since:
                continue

            user = item.get("user")
            if self.filter_helper.filter_bot(user, filters):
                continue

            # For Issues API response, we need to fetch PR details for branch filters
            if author:
                # Skip branch filter check for Issues API (lightweight)
                pass
            elif not self.pr_matches_branch_filters(item, filters):
                continue

            pr_titles.append(
                {
                    "number": item.get("number", 0),
                    "title": item.get("title", ""),
                    "author": (item.get("user") or {}).get("login", ""),
                    "url": item.get("html_url", ""),
                    "state": item.get("state", ""),
                    "additions": item.get("additions", 0),
                    "deletions": item.get("deletions", 0),
                }
            )

            if len(pr_titles) >= limit:
                break

        return pr_titles[:limit]

    def collect_pull_request_details(
        self, repo: str, number: int
    ) -> PullRequestReviewBundle:
        """Gather detailed information for a single pull request.

        Args:
            repo: Repository name (owner/repo)
            number: Pull request number

        Returns:
            PullRequestReviewBundle with all PR details
        """
        pr_payload = self.api_client.request_json(f"repos/{repo}/pulls/{number}")
        review_payload = self.api_client.request_all(
            f"repos/{repo}/pulls/{number}/reviews",
            build_pagination_params(),
        )
        review_comment_payload = self.api_client.request_all(
            f"repos/{repo}/pulls/{number}/comments",
            build_pagination_params(),
        )
        files_payload = self.api_client.request_all(
            f"repos/{repo}/pulls/{number}/files",
            build_pagination_params(),
        )

        created_at_raw = pr_payload.get(
            "created_at", datetime.now(timezone.utc).isoformat()
        )
        updated_at_raw = pr_payload.get("updated_at", created_at_raw)

        repo_root = self.config.server.web_url.rstrip("/")
        html_url = pr_payload.get(
            "html_url",
            f"{repo_root}/{repo}/pull/{number}",
        )

        files: List[PullRequestFile] = []
        for entry in files_payload:
            files.append(
                PullRequestFile(
                    filename=entry.get("filename", ""),
                    status=entry.get("status", "modified"),
                    additions=int(entry.get("additions", 0) or 0),
                    deletions=int(entry.get("deletions", 0) or 0),
                    changes=int(entry.get("changes", 0) or 0),
                    patch=entry.get("patch"),
                )
            )

        review_bodies = [
            review.get("body", "").strip()
            for review in review_payload
            if review.get("body")
        ]
        review_comments = [
            comment.get("body", "").strip()
            for comment in review_comment_payload
            if comment.get("body")
        ]

        return PullRequestReviewBundle(
            repo=repo,
            number=number,
            title=pr_payload.get("title", ""),
            body=pr_payload.get("body", ""),
            author=(pr_payload.get("user") or {}).get("login", ""),
            html_url=html_url,
            created_at=self.parse_timestamp(created_at_raw).astimezone(timezone.utc),
            updated_at=self.parse_timestamp(updated_at_raw).astimezone(timezone.utc),
            additions=int(pr_payload.get("additions", 0) or 0),
            deletions=int(pr_payload.get("deletions", 0) or 0),
            changed_files=int(pr_payload.get("changed_files", 0) or len(files)),
            review_bodies=review_bodies,
            review_comments=review_comments,
            files=files,
        )

    def list_authored_pull_requests(
        self, repo: str, author: str, state: str = "all"
    ) -> List[int]:
        """Return PR numbers where the user is the author.

        Args:
            repo: Repository name (owner/repo)
            author: GitHub username
            state: PR state filter (open/closed/all)

        Returns:
            List of PR numbers

        Raises:
            ValueError: If state is not valid
        """
        state_normalised = state.lower().strip() or "all"
        if state_normalised not in {"open", "closed", "all"}:
            raise ValueError("state must be one of 'open', 'closed', or 'all'")

        params = build_list_params(state=state_normalised, creator=author)

        issues = self.api_client.request_all(f"repos/{repo}/issues", params)
        numbers: List[int] = []
        seen: Set[int] = set()
        for issue in issues:
            if "pull_request" not in issue:
                continue
            number = int(issue.get("number", 0) or 0)
            if not number or number in seen:
                continue
            seen.add(number)
            numbers.append(number)

        return numbers
