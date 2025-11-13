"""GitHub data collection layer with facade pattern."""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Iterable, List, Optional

import requests

from .analytics_collector import AnalyticsCollector
from .api_client import GitHubApiClient
from .commit_collector import CommitCollector
from .config import Config
from .console import Console
from .issue_collector import IssueCollector
from .models import (
    AnalysisFilters,
    CollectionResult,
    PullRequestReviewBundle,
    PullRequestSummary,
)
from .pr_collector import PullRequestCollector
from .repository_manager import RepositoryManager
from .review_collector import ReviewCollector

logger = logging.getLogger(__name__)
console = Console()


# ============================================================================
# Helper Functions for Error Handling
# ============================================================================

def handle_future_result(future, task_name: str, repo: str, timeout: int, default_value):
    """Handle future result with timeout and error handling.

    Args:
        future: The future to await
        task_name: Name of the task for logging
        repo: Repository name for logging
        timeout: Timeout in seconds
        default_value: Default value to return on error

    Returns:
        Result from future or default_value on error/timeout
    """
    try:
        return future.result(timeout=timeout)
    except TimeoutError:
        logger.warning(f"{task_name} timed out after {timeout}s for {repo}")
        console.log(f"[warning]⚠ {task_name} timed out - data may be incomplete")
        return default_value
    except Exception as exc:
        logger.error(f"{task_name} failed for {repo}: {exc}")
        console.log(f"[warning]⚠ {task_name} failed: {type(exc).__name__}")
        return default_value


@dataclass
class Collector:
    """Facade for GitHub data collection using specialized collectors.

    This class delegates to specialized collectors while maintaining
    backward compatibility with the original API.
    """

    config: Config
    session: Optional[requests.Session] = None

    def __post_init__(self) -> None:
        """Initialize the facade and all specialized collectors."""
        # Create API client (Repository pattern)
        self.api_client = GitHubApiClient(self.config, self.session)

        # Create specialized collectors
        self.commit_collector = CommitCollector(self.config, self.api_client)
        self.pr_collector = PullRequestCollector(self.config, self.api_client)
        self.review_collector = ReviewCollector(self.config, self.api_client)
        self.issue_collector = IssueCollector(self.config, self.api_client)
        self.analytics_collector = AnalyticsCollector(self.config, self.api_client)
        self.repository_manager = RepositoryManager(self.api_client)

    def collect(
        self,
        repo: str,
        months: int,
        filters: Optional[AnalysisFilters] = None,
        author: Optional[str] = None,
    ) -> CollectionResult:
        """Collect repository artefacts via the GitHub REST API.

        Args:
            repo: Repository name (owner/repo)
            months: Number of months to collect data for
            filters: Optional analysis filters
            author: Optional GitHub username to filter by author (for personal activity tracking)

        Returns:
            CollectionResult with all collected data
        """
        filters = filters or AnalysisFilters()

        console.log(
            "Collecting GitHub data (parallel mode)",
            f"repo={repo}",
            f"months={months}",
            f"author={author or 'all'}",
        )

        since = datetime.now(timezone.utc) - timedelta(days=30 * max(months, 1))
        until = datetime.now(timezone.utc)

        # Phase 1: Parallel collection of independent data
        # (commits, PRs, and issues can be collected in parallel)
        # Import timeout constant from constants module
        from .constants import PARALLEL_CONFIG

        collection_timeout = PARALLEL_CONFIG['collection_timeout']

        with ThreadPoolExecutor(max_workers=3) as executor:
            console.log("Phase 1: Collecting commits, PRs, and issues in parallel")

            future_commits = executor.submit(
                self.commit_collector.count_commits, repo, since, filters, author
            )
            future_prs = executor.submit(
                self.pr_collector.list_pull_requests, repo, since, filters, author
            )
            future_issues = executor.submit(
                self.issue_collector.count_issues, repo, since, filters, author
            )

            # Wait for all to complete with timeout using helper
            commits = handle_future_result(
                future_commits, "Commit collection", repo, collection_timeout, 0
            )
            pull_requests, pr_metadata = handle_future_result(
                future_prs, "PR collection", repo, collection_timeout, (0, [])
            )
            issues = handle_future_result(
                future_issues, "Issue collection", repo, collection_timeout, 0
            )

        console.log(
            "Phase 1 complete",
            f"commits={commits}",
            f"pull_requests={pull_requests}",
            f"issues={issues}",
        )

        # Phase 2: Process dependent data in parallel
        # (PR examples and reviews depend on pr_metadata)
        with ThreadPoolExecutor(max_workers=2) as executor:
            console.log("Phase 2: Building PR examples and counting reviews in parallel")

            future_examples = executor.submit(
                self.pr_collector.build_pull_request_examples, pr_metadata
            )
            future_reviews = executor.submit(
                self.review_collector.count_reviews, repo, pr_metadata, since, filters
            )

            # Wait for all to complete with timeout using helper
            pull_request_examples = handle_future_result(
                future_examples, "PR examples building", repo, collection_timeout, []
            )
            reviews = handle_future_result(
                future_reviews, "Review collection", repo, collection_timeout, 0
            )

        console.log("Phase 2 complete", f"reviews={reviews}")

        return CollectionResult(
            repo=repo,
            months=months,
            collected_at=datetime.now(timezone.utc),
            commits=commits,
            pull_requests=pull_requests,
            reviews=reviews,
            issues=issues,
            filters=filters,
            pull_request_examples=pull_request_examples,
            since_date=since,
            until_date=until,
        )

    # Commit-related methods
    def collect_commit_messages(
        self,
        repo: str,
        since: datetime,
        filters: Optional[AnalysisFilters] = None,
        limit: int = 100,
        author: Optional[str] = None,
    ) -> List[Dict[str, str]]:
        """Collect commit messages for quality analysis."""
        return self.commit_collector.collect_commit_messages(
            repo, since, filters, limit, author
        )

    # Pull request methods
    def list_pull_requests(
        self,
        repo: str,
        since: datetime,
        filters: Optional[AnalysisFilters] = None,
        author: Optional[str] = None,
    ) -> tuple[int, List[Dict[str, Any]]]:
        """List pull requests with metadata.

        Args:
            repo: Repository name (owner/repo)
            since: Start date for PR collection
            filters: Optional analysis filters
            author: Optional GitHub username to filter PRs by author

        Returns:
            Tuple of (PR count, PR metadata list)
        """
        return self.pr_collector.list_pull_requests(repo, since, filters, author)

    def list_authored_pull_requests(
        self, repo: str, author: str, state: str = "all"
    ) -> List[int]:
        """Return pull request numbers where the user is the author."""
        return self.pr_collector.list_authored_pull_requests(repo, author, state)

    def collect_pull_request_details(
        self, repo: str, number: int
    ) -> PullRequestReviewBundle:
        """Gather detailed information for a single pull request."""
        console.log(
            "Collecting pull request artefacts",
            f"repo={repo}",
            f"number={number}",
        )
        return self.pr_collector.collect_pull_request_details(repo, number)

    def collect_pr_titles(
        self,
        repo: str,
        since: datetime,
        filters: Optional[AnalysisFilters] = None,
        limit: int = 100,
        author: Optional[str] = None,
    ) -> List[Dict[str, str]]:
        """Collect pull request titles for quality analysis."""
        return self.pr_collector.collect_pr_titles(repo, since, filters, limit, author)

    # Review methods
    def get_authenticated_user(self) -> str:
        """Return the username of the authenticated user (PAT owner)."""
        return self.review_collector.get_authenticated_user()

    def collect_review_comments_detailed(
        self,
        repo: str,
        since: datetime,
        filters: Optional[AnalysisFilters] = None,
        limit: int = 100,
        author: Optional[str] = None,
    ) -> List[Dict[str, str]]:
        """Collect review comments for tone analysis."""
        return self.review_collector.collect_review_comments_detailed(
            repo, since, filters, limit, author
        )

    # Issue methods
    def collect_issue_details(
        self,
        repo: str,
        since: datetime,
        filters: Optional[AnalysisFilters] = None,
        limit: int = 100,
        author: Optional[str] = None,
    ) -> List[Dict[str, str]]:
        """Collect issue details for quality analysis."""
        return self.issue_collector.collect_issue_details(repo, since, filters, limit, author)

    # Analytics methods
    def collect_monthly_trends(
        self,
        repo: str,
        since: datetime,
        filters: Optional[AnalysisFilters] = None,
    ) -> List[Dict[str, Any]]:
        """Collect monthly activity trends for time-series analysis."""
        return self.analytics_collector.collect_monthly_trends(repo, since, filters)

    def collect_tech_stack(
        self,
        repo: str,
        pr_metadata: List[Dict[str, Any]],
    ) -> Dict[str, int]:
        """Analyze technology stack from PR file changes."""
        return self.analytics_collector.collect_tech_stack(repo, pr_metadata)

    def collect_collaboration_network(
        self,
        repo: str,
        pr_metadata: List[Dict[str, Any]],
        filters: Optional[AnalysisFilters] = None,
    ) -> Dict[str, Any]:
        """Analyze collaboration patterns from PR reviews."""
        return self.analytics_collector.collect_collaboration_network(
            repo, pr_metadata, filters
        )

    # Repository management methods
    def list_user_repositories(
        self,
        sort: str = "updated",
        affiliation: str = "owner,collaborator,organization_member",
    ) -> List[Dict[str, Any]]:
        """List repositories accessible to the authenticated user.

        Args:
            sort: Sort field (created, updated, pushed, full_name)
            affiliation: Comma-separated list of affiliation types

        Returns:
            List of repository dictionaries with metadata
        """
        return self.repository_manager.get_user_repositories(sort, affiliation)

    def list_org_repositories(
        self, org: str, sort: str = "updated"
    ) -> List[Dict[str, Any]]:
        """List repositories for a specific organization.

        Args:
            org: Organization name
            sort: Sort field (created, updated, pushed, full_name)

        Returns:
            List of repository dictionaries
        """
        return self.repository_manager.get_org_repositories(org, sort)

    def list_user_organizations(self) -> List[Dict[str, Any]]:
        """List organizations the authenticated user belongs to.

        Returns:
            List of organization dictionaries
        """
        return self.repository_manager.get_user_organizations()

    def suggest_repositories(
        self,
        limit: int = 10,
        min_activity_days: int = 90,
        sort_by: str = "updated",
    ) -> List[Dict[str, Any]]:
        """Suggest repositories for analysis based on activity and recency.

        Args:
            limit: Maximum number of suggestions
            min_activity_days: Filter repos updated within this many days
            sort_by: Sorting criteria (updated, stars, activity)

        Returns:
            List of suggested repository dictionaries with metadata
        """
        return self.repository_manager.suggest_repositories(
            limit, min_activity_days, sort_by
        )

    def search_repositories(
        self, query: str, sort: str = "stars", limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search for repositories matching a query.

        Args:
            query: Search query string
            sort: Sort field (stars, forks, help-wanted-issues, updated)
            limit: Maximum number of results to return

        Returns:
            List of repository dictionaries
        """
        return self.repository_manager.search_repositories(query, sort, limit)

    def close(self) -> None:
        """Close API client and release resources."""
        if hasattr(self, 'api_client') and self.api_client is not None:
            self.api_client.close()

    def __enter__(self) -> "Collector":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit - close resources."""
        self.close()
