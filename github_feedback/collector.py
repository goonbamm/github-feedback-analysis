"""GitHub data collection layer."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Iterable, List, Optional

import requests

from .config import Config
from .console import Console
from .models import AnalysisFilters, CollectionResult

console = Console()


@dataclass(slots=True)
class Collector:
    """High-level wrapper around GitHub API collection."""

    config: Config
    session: Optional[requests.Session] = None
    _headers: Dict[str, str] = field(init=False, default_factory=dict)

    def __post_init__(self) -> None:
        if self.config.auth is None or not self.config.auth.pat:
            raise ValueError("Authentication PAT is not configured. Run `gf init` first.")

        self._headers = {
            "Authorization": f"Bearer {self.config.auth.pat}",
            "Accept": "application/vnd.github+json",
        }

    def collect(
        self,
        repo: str,
        months: int,
        filters: Optional[AnalysisFilters] = None,
    ) -> CollectionResult:
        """Collect repository artefacts via the GitHub REST API."""

        filters = filters or AnalysisFilters()

        console.log("Collecting GitHub data", repo=repo, months=months)

        since = datetime.now(timezone.utc) - timedelta(days=30 * max(months, 1))

        commits = self._count_commits(repo, since, filters)
        pull_requests, pr_metadata = self._list_pull_requests(repo, since, filters)
        reviews = self._count_reviews(repo, pr_metadata, since, filters)
        issues = self._count_issues(repo, since, filters)

        return CollectionResult(
            repo=repo,
            months=months,
            collected_at=datetime.utcnow(),
            commits=commits,
            pull_requests=pull_requests,
            reviews=reviews,
            issues=issues,
            filters=filters,
        )

    # Internal helpers -------------------------------------------------

    def _get_session(self) -> requests.Session:
        if self.session is None:
            self.session = requests.Session()
            self.session.headers.update(self._headers)
        return self.session

    def _build_api_url(self, path: str) -> str:
        base = self.config.server.api_url.rstrip("/")
        return f"{base}/{path.lstrip('/')}"

    def _request(self, path: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        response = self._get_session().get(
            self._build_api_url(path),
            params=params,
            timeout=30,
            verify=self.config.server.verify_ssl,
        )
        if response.status_code == 401:
            raise PermissionError("GitHub API rejected the provided PAT.")
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, list):
            raise ValueError(f"Unexpected payload type for {path}: {type(payload)!r}")
        return payload

    @staticmethod
    def _parse_timestamp(value: str) -> datetime:
        if value.endswith("Z"):
            value = value.replace("Z", "+00:00")
        return datetime.fromisoformat(value)

    def _filter_bot(self, author: Optional[Dict[str, Any]], filters: AnalysisFilters) -> bool:
        if not filters.exclude_bots:
            return False
        if not author:
            return False
        return author.get("type") == "Bot"

    def _count_commits(
        self, repo: str, since: datetime, filters: AnalysisFilters
    ) -> int:
        total = 0
        page = 1
        params: Dict[str, Any] = {
            "since": since.isoformat(),
            "per_page": 100,
        }
        if filters.include_branches:
            params["sha"] = filters.include_branches[0]

        while True:
            page_params = params | {"page": page}
            data = self._request(f"repos/{repo}/commits", page_params)
            if not data:
                break
            for commit in data:
                author = commit.get("author")
                if self._filter_bot(author, filters):
                    continue
                total += 1
            if len(data) < 100:
                break
            page += 1
        return total

    def _list_pull_requests(
        self, repo: str, since: datetime, filters: AnalysisFilters
    ) -> tuple[int, List[Dict[str, Any]]]:
        total = 0
        page = 1
        metadata: List[Dict[str, Any]] = []
        params: Dict[str, Any] = {
            "state": "all",
            "per_page": 100,
            "sort": "created",
            "direction": "desc",
        }

        stop_pagination = False
        while not stop_pagination:
            page_params = params | {"page": page}
            data = self._request(f"repos/{repo}/pulls", page_params)
            if not data:
                break
            for pr in data:
                created_at = self._parse_timestamp(pr["created_at"]).astimezone(timezone.utc)
                if created_at < since:
                    stop_pagination = True
                    break
                author = pr.get("user")
                if self._filter_bot(author, filters):
                    continue
                total += 1
                metadata.append(pr)
            if len(data) < 100:
                break
            page += 1
        return total, metadata

    def _count_reviews(
        self,
        repo: str,
        pull_requests: Iterable[Dict[str, Any]],
        since: datetime,
        filters: AnalysisFilters,
    ) -> int:
        total = 0
        for pr in pull_requests:
            number = pr["number"]
            page = 1
            while True:
                data = self._request(
                    f"repos/{repo}/pulls/{number}/reviews",
                    {"per_page": 100, "page": page},
                )
                if not data:
                    break
                for review in data:
                    submitted_at = review.get("submitted_at")
                    if submitted_at:
                        submitted_dt = self._parse_timestamp(submitted_at).astimezone(timezone.utc)
                        if submitted_dt < since:
                            continue
                    author = review.get("user")
                    if self._filter_bot(author, filters):
                        continue
                    total += 1
                if len(data) < 100:
                    break
                page += 1
        return total

    def _count_issues(
        self, repo: str, since: datetime, filters: AnalysisFilters
    ) -> int:
        total = 0
        page = 1
        params: Dict[str, Any] = {
            "state": "all",
            "per_page": 100,
            "since": since.isoformat(),
        }
        while True:
            page_params = params | {"page": page}
            data = self._request(f"repos/{repo}/issues", page_params)
            if not data:
                break
            for issue in data:
                if "pull_request" in issue:
                    continue
                author = issue.get("user")
                if self._filter_bot(author, filters):
                    continue
                total += 1
            if len(data) < 100:
                break
            page += 1
        return total
