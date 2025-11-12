"""Pull request collection operations."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set

from .base_collector import BaseCollector
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
        self, repo: str, since: datetime, filters: AnalysisFilters
    ) -> tuple[int, List[Dict[str, Any]]]:
        """List pull requests matching filters.

        Args:
            repo: Repository name (owner/repo)
            since: Start date for PR collection
            filters: Analysis filters to apply

        Returns:
            Tuple of (count, metadata list)
        """
        params: Dict[str, Any] = {
            "state": "all",
            "per_page": 100,
            "sort": "created",
            "direction": "desc",
        }

        pr_file_cache: Dict[int, List[Dict[str, Any]]] = {}

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

        # Apply filters
        metadata: List[Dict[str, Any]] = []
        for pr in all_prs:
            author = pr.get("user")
            if self.filter_bot(author, filters):
                continue
            if not self.pr_matches_branch_filters(pr, filters):
                continue
            if not self._pr_matches_file_filters(repo, pr, filters, pr_file_cache):
                continue
            metadata.append(pr)

        return len(metadata), metadata

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
    ) -> List[Dict[str, str]]:
        """Collect PR titles for quality analysis.

        Args:
            repo: Repository name (owner/repo)
            since: Start date for PR collection
            filters: Optional analysis filters
            limit: Maximum number of PRs to collect

        Returns:
            List of PR title dictionaries
        """
        filters = filters or AnalysisFilters()
        pr_titles: List[Dict[str, str]] = []

        params: Dict[str, Any] = {
            "state": "all",
            "sort": "created",
            "direction": "desc",
            "per_page": limit,
        }

        data = self.api_client.request_list(f"repos/{repo}/pulls", params)
        for pr in data:
            created_at_raw = pr.get("created_at")
            if not created_at_raw:
                continue

            created_at = self.parse_timestamp(created_at_raw).astimezone(timezone.utc)
            if created_at < since:
                continue

            author = pr.get("user")
            if self.filter_bot(author, filters):
                continue

            if not self.pr_matches_branch_filters(pr, filters):
                continue

            pr_titles.append(
                {
                    "number": pr.get("number", 0),
                    "title": pr.get("title", ""),
                    "author": (pr.get("user") or {}).get("login", ""),
                    "url": pr.get("html_url", ""),
                    "state": pr.get("state", ""),
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
            {"per_page": 100},
        )
        review_comment_payload = self.api_client.request_all(
            f"repos/{repo}/pulls/{number}/comments",
            {"per_page": 100},
        )
        files_payload = self.api_client.request_all(
            f"repos/{repo}/pulls/{number}/files",
            {"per_page": 100},
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

        params = {
            "creator": author,
            "state": state_normalised,
            "per_page": 100,
        }

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

    def _pr_matches_file_filters(
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
