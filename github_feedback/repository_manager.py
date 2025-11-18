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
        self._current_user: Optional[Dict[str, Any]] = None
        self._user_contributions_cache: Dict[str, int] = {}

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

    def _get_current_user(self) -> Dict[str, Any]:
        """Get current authenticated user info (cached).

        Returns:
            User information dictionary
        """
        if self._current_user is None:
            self._current_user = self.api_client.get_authenticated_user()
        return self._current_user

    def _get_user_contribution_count(self, repo: Dict[str, Any]) -> int:
        """Get the number of commits by the current user in a repository.

        Args:
            repo: Repository dictionary

        Returns:
            Number of commits by the user (0 if none or error)
        """
        full_name = repo.get("full_name", "")
        if not full_name:
            return 0

        # Check cache first
        if full_name in self._user_contributions_cache:
            return self._user_contributions_cache[full_name]

        try:
            owner, repo_name = full_name.split("/", 1)
            username = self._get_current_user().get("login", "")
            if not username:
                return 0

            # Fetch only first page (100 commits) for performance
            commits = self.api_client.get_user_commits_in_repo(
                owner, repo_name, username, max_pages=1
            )
            commit_count = len(commits)

            # Cache the result
            self._user_contributions_cache[full_name] = commit_count
            return commit_count

        except Exception:
            # If there's any error (e.g., no access, API error), return 0
            self._user_contributions_cache[full_name] = 0
            return 0

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

        # Enrich all active repos with contribution data BEFORE sorting
        for repo in active_repos:
            repo["_user_commits"] = self._get_user_contribution_count(repo)

        # Sort by requested criteria (now including user contributions)
        if sort_by == "stars":
            active_repos.sort(
                key=lambda r: r.get("stargazers_count", 0), reverse=True
            )
        elif sort_by == "activity":
            # Sort by a combination of factors: recent updates, stars, forks, AND user contributions
            active_repos.sort(
                key=lambda r: (
                    r.get("stargazers_count", 0) * 0.3
                    + r.get("forks_count", 0) * 0.3
                    + r.get("_user_commits", 0) * 10  # Heavy weight for user contributions
                    + (1 if not r.get("archived", False) else 0) * 100
                ),
                reverse=True,
            )
        else:
            # For "updated" sort (default), also consider user contributions
            # Repositories with user commits should be prioritized
            active_repos.sort(
                key=lambda r: (
                    r.get("_user_commits", 0) * 1000,  # Primary: user has contributed
                    datetime.fromisoformat(r.get("updated_at", "1970-01-01T00:00:00Z").replace("Z", "+00:00")).replace(tzinfo=None)
                ),
                reverse=True,
            )

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

        # MAJOR BOOST: User has contributed to this repository
        user_commits = repo.get("_user_commits", 0)
        if user_commits > 0:
            # Base contribution bonus
            score += 100
            # Additional points based on number of commits (capped at 100 commits)
            score += min(user_commits, 100) * 5

        # Factor in stars (less weight if user hasn't contributed)
        star_weight = 0.1 if user_commits > 0 else 0.05
        score += repo.get("stargazers_count", 0) * star_weight

        # Factor in forks (less weight if user hasn't contributed)
        fork_weight = 0.15 if user_commits > 0 else 0.08
        score += repo.get("forks_count", 0) * fork_weight

        # Factor in open issues (indicates activity)
        score += repo.get("open_issues_count", 0) * 0.05

        # Penalty for archived repos
        if repo.get("archived", False):
            score *= 0.1

        # Bonus for non-fork repos (original work) - only if user contributed
        if not repo.get("fork", False) and user_commits > 0:
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

    def get_year_in_review_repositories(
        self,
        year: Optional[int] = None,
        min_contributions: int = 3,
    ) -> List[Dict[str, Any]]:
        """Get repositories the user actively contributed to in a specific year.

        Args:
            year: Year to analyze (default: current year)
            min_contributions: Minimum number of contributions to include repo

        Returns:
            List of repositories with contribution metadata
        """
        if year is None:
            year = datetime.now().year

        # Calculate date range for the year
        start_date = datetime(year, 1, 1)
        end_date = datetime(year, 12, 31, 23, 59, 59)

        # Fetch all user repositories
        all_repos = self.get_user_repositories(sort="updated")

        # Get current user
        username = self._get_current_user().get("login", "")
        if not username:
            return []

        active_repos = []

        for repo in all_repos:
            full_name = repo.get("full_name", "")
            if not full_name:
                continue

            try:
                owner, repo_name = full_name.split("/", 1)

                # Get commits in the specified year
                params = {
                    "author": username,
                    "since": start_date.isoformat() + "Z",
                    "until": end_date.isoformat() + "Z",
                    "per_page": 100,
                }

                commits = self.api_client.request_all(
                    f"/repos/{owner}/{repo_name}/commits",
                    params=params,
                )

                commit_count = len(commits)

                # Include repo if it meets minimum contribution threshold
                if commit_count >= min_contributions:
                    repo["_year_commits"] = commit_count
                    repo["_year"] = year
                    active_repos.append(repo)

            except Exception:
                # Skip repos that fail (permissions, deleted, etc.)
                continue

        # Sort by number of contributions in descending order
        active_repos.sort(key=lambda r: r.get("_year_commits", 0), reverse=True)

        return active_repos

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
