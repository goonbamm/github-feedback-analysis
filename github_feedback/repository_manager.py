"""Repository discovery and suggestions manager."""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from github_feedback.api_client import GitHubApiClient


class RepositoryManager:
    """Handle repository discovery and suggestions for GitHub repositories."""

    def __init__(self, api_client: GitHubApiClient):
        """Initialize repository manager.

        Args:
            api_client: GitHub API client instance
        """
        self.api_client = api_client

    def get_user_repositories(
        self,
        sort: str = "updated",
        affiliation: str = "owner,collaborator,organization_member",
        per_page: int = 100,
    ) -> List[Dict[str, Any]]:
        """Fetch repositories accessible to the authenticated user.

        Args:
            sort: Sort field (created, updated, pushed, full_name)
            affiliation: Comma-separated list of affiliation types
            per_page: Number of results per page

        Returns:
            List of repository dictionaries with metadata
        """
        params = {
            "sort": sort,
            "affiliation": affiliation,
            "per_page": per_page,
        }

        repos = self.api_client.request_all("/user/repos", params=params)
        return repos

    def get_org_repositories(
        self, org: str, sort: str = "updated", per_page: int = 100
    ) -> List[Dict[str, Any]]:
        """Fetch repositories for a specific organization.

        Args:
            org: Organization name
            sort: Sort field (created, updated, pushed, full_name)
            per_page: Number of results per page

        Returns:
            List of repository dictionaries
        """
        params = {
            "sort": sort,
            "per_page": per_page,
        }

        repos = self.api_client.request_all(f"/orgs/{org}/repos", params=params)
        return repos

    def get_user_organizations(self) -> List[Dict[str, Any]]:
        """Fetch organizations the authenticated user belongs to.

        Returns:
            List of organization dictionaries
        """
        orgs = self.api_client.request_all("/user/orgs")
        return orgs

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
        params = {
            "q": query,
            "sort": sort,
            "per_page": min(limit, 100),
        }

        result = self.api_client.request_json("/search/repositories", params=params)
        items = result.get("items", [])
        return items[:limit]

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
        # Fetch user's repositories sorted by update time
        all_repos = self.get_user_repositories(sort="updated")

        # Filter by recent activity
        cutoff_date = datetime.now() - timedelta(days=min_activity_days)
        active_repos = []

        for repo in all_repos:
            # Parse updated_at timestamp
            updated_at_str = repo.get("updated_at", "")
            if updated_at_str:
                try:
                    # GitHub returns ISO 8601 format: 2024-01-15T10:30:00Z
                    updated_at = datetime.fromisoformat(
                        updated_at_str.replace("Z", "+00:00")
                    )
                    # Convert to naive datetime for comparison
                    updated_at = updated_at.replace(tzinfo=None)

                    if updated_at >= cutoff_date:
                        active_repos.append(repo)
                except (ValueError, AttributeError):
                    # If parsing fails, skip this repo
                    continue

        # Sort by requested criteria
        if sort_by == "stars":
            active_repos.sort(
                key=lambda r: r.get("stargazers_count", 0), reverse=True
            )
        elif sort_by == "activity":
            # Sort by a combination of factors: recent updates, stars, forks
            active_repos.sort(
                key=lambda r: (
                    r.get("stargazers_count", 0) * 0.3
                    + r.get("forks_count", 0) * 0.3
                    + (1 if not r.get("archived", False) else 0) * 100
                ),
                reverse=True,
            )
        # Default is already sorted by 'updated'

        # Return top N suggestions
        suggestions = active_repos[:limit]

        # Enrich with calculated fields for display
        for repo in suggestions:
            repo["_suggestion_score"] = self._calculate_suggestion_score(repo)

        return suggestions

    def _calculate_suggestion_score(self, repo: Dict[str, Any]) -> float:
        """Calculate a suggestion score for a repository.

        Args:
            repo: Repository dictionary

        Returns:
            Suggestion score (higher is better)
        """
        score = 0.0

        # Factor in stars
        score += repo.get("stargazers_count", 0) * 0.1

        # Factor in forks
        score += repo.get("forks_count", 0) * 0.15

        # Factor in open issues (indicates activity)
        score += repo.get("open_issues_count", 0) * 0.05

        # Penalty for archived repos
        if repo.get("archived", False):
            score *= 0.1

        # Bonus for non-fork repos (original work)
        if not repo.get("fork", False):
            score *= 1.2

        # Recency bonus (updated in last 30 days)
        updated_at_str = repo.get("updated_at", "")
        if updated_at_str:
            try:
                updated_at = datetime.fromisoformat(updated_at_str.replace("Z", "+00:00"))
                updated_at = updated_at.replace(tzinfo=None)
                days_since_update = (datetime.now() - updated_at).days

                if days_since_update <= 30:
                    score *= 1.5
                elif days_since_update <= 60:
                    score *= 1.2
            except (ValueError, AttributeError):
                pass

        return score

    def format_repository_summary(self, repo: Dict[str, Any]) -> str:
        """Format a repository as a summary string for display.

        Args:
            repo: Repository dictionary

        Returns:
            Formatted summary string
        """
        full_name = repo.get("full_name", "unknown/repo")
        description = repo.get("description", "No description")
        stars = repo.get("stargazers_count", 0)
        forks = repo.get("forks_count", 0)
        updated_at = repo.get("updated_at", "")

        # Truncate description if too long
        if len(description) > 60:
            description = description[:57] + "..."

        # Format updated date
        updated_str = ""
        if updated_at:
            try:
                updated_dt = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
                updated_dt = updated_dt.replace(tzinfo=None)
                days_ago = (datetime.now() - updated_dt).days

                if days_ago == 0:
                    updated_str = "today"
                elif days_ago == 1:
                    updated_str = "yesterday"
                elif days_ago < 30:
                    updated_str = f"{days_ago}d ago"
                elif days_ago < 365:
                    updated_str = f"{days_ago // 30}mo ago"
                else:
                    updated_str = f"{days_ago // 365}y ago"
            except (ValueError, AttributeError):
                updated_str = "unknown"

        return f"{full_name} - {description} (⭐ {stars}, 🍴 {forks}, 📅 {updated_str})"
