"""GitHub data collection layer with facade pattern."""

from __future__ import annotations

import logging
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
from .review_collector import ReviewCollector

logger = logging.getLogger(__name__)
console = Console()


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

    def collect(
        self,
        repo: str,
        months: int,
        filters: Optional[AnalysisFilters] = None,
    ) -> CollectionResult:
        """Collect repository artefacts via the GitHub REST API.

        Args:
            repo: Repository name (owner/repo)
            months: Number of months to collect data for
            filters: Optional analysis filters

        Returns:
            CollectionResult with all collected data
        """
        filters = filters or AnalysisFilters()

        console.log(
            "Collecting GitHub data",
            f"repo={repo}",
            f"months={months}",
        )

        since = datetime.now(timezone.utc) - timedelta(days=30 * max(months, 1))
        until = datetime.now(timezone.utc)

        # Delegate to specialized collectors
        commits = self.commit_collector.count_commits(repo, since, filters)
        pull_requests, pr_metadata = self.pr_collector.list_pull_requests(
            repo, since, filters
        )
        pull_request_examples = self.pr_collector.build_pull_request_examples(
            pr_metadata
        )
        reviews = self.review_collector.count_reviews(repo, pr_metadata, since, filters)
        issues = self.issue_collector.count_issues(repo, since, filters)

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
    ) -> List[Dict[str, str]]:
        """Collect commit messages for quality analysis."""
        return self.commit_collector.collect_commit_messages(
            repo, since, filters, limit
        )

    # Pull request methods
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
    ) -> List[Dict[str, str]]:
        """Collect pull request titles for quality analysis."""
        return self.pr_collector.collect_pr_titles(repo, since, filters, limit)

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
    ) -> List[Dict[str, str]]:
        """Collect review comments for tone analysis."""
        return self.review_collector.collect_review_comments_detailed(
            repo, since, filters, limit
        )

    # Issue methods
    def collect_issue_details(
        self,
        repo: str,
        since: datetime,
        filters: Optional[AnalysisFilters] = None,
        limit: int = 100,
    ) -> List[Dict[str, str]]:
        """Collect issue details for quality analysis."""
        return self.issue_collector.collect_issue_details(repo, since, filters, limit)

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
