"""GitHub data collection layer."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Set

import requests

from .config import Config
from .console import Console
from .models import (
    AnalysisFilters,
    CollectionResult,
    PullRequestFile,
    PullRequestReviewBundle,
    PullRequestSummary,
)

logger = logging.getLogger(__name__)


LANGUAGE_EXTENSION_MAP: Dict[str, str] = {
    "py": "Python",
    "js": "JavaScript",
    "ts": "TypeScript",
    "tsx": "TypeScript",
    "jsx": "JavaScript",
    "rb": "Ruby",
    "go": "Go",
    "rs": "Rust",
    "java": "Java",
    "cs": "C#",
    "cpp": "C++",
    "cxx": "C++",
    "cc": "C++",
    "c": "C",
    "kt": "Kotlin",
    "swift": "Swift",
    "php": "PHP",
    "scala": "Scala",
    "m": "Objective-C",
    "mm": "Objective-C++",
    "hs": "Haskell",
    "r": "R",
    "pl": "Perl",
    "sh": "Shell",
    "ps1": "PowerShell",
    "dart": "Dart",
    "md": "Markdown",
    "yml": "YAML",
    "yaml": "YAML",
    "json": "JSON",
}

console = Console()


@dataclass(slots=True)
class Collector:
    """High-level wrapper around GitHub API collection."""

    config: Config
    session: Optional[requests.Session] = None
    _headers: Dict[str, str] = field(init=False, default_factory=dict)
    _request: Callable[[str, Optional[Dict[str, Any]]], List[Dict[str, Any]]] = field(
        init=False, repr=False
    )
    _request_json: Callable[[str, Optional[Dict[str, Any]]], Dict[str, Any]] = field(
        init=False, repr=False
    )

    def __post_init__(self) -> None:
        pat = self.config.get_pat()
        if not pat:
            raise ValueError("Authentication PAT is not configured. Run `ghf init` first.")

        self._headers = {
            "Authorization": f"Bearer {pat}",
            "Accept": "application/vnd.github+json",
        }
        object.__setattr__(self, "_request", self._request_impl)
        object.__setattr__(self, "_request_json", self._request_json_impl)

    def collect(
        self,
        repo: str,
        months: int,
        filters: Optional[AnalysisFilters] = None,
    ) -> CollectionResult:
        """Collect repository artefacts via the GitHub REST API."""

        filters = filters or AnalysisFilters()

        console.log(
            "Collecting GitHub data",
            f"repo={repo}",
            f"months={months}",
        )

        since = datetime.now(timezone.utc) - timedelta(days=30 * max(months, 1))

        commits = self._count_commits(repo, since, filters)
        pull_requests, pr_metadata = self._list_pull_requests(repo, since, filters)
        pull_request_examples = self._build_pull_request_examples(pr_metadata)
        reviews = self._count_reviews(repo, pr_metadata, since, filters)
        issues = self._count_issues(repo, since, filters)

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

    def _request_impl(
        self, path: str, params: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        response = self._get_session().get(
            self._build_api_url(path),
            params=params,
            timeout=30,
        )
        if response.status_code == 401:
            raise PermissionError("GitHub API rejected the provided PAT.")
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, list):
            raise ValueError(f"Unexpected payload type for {path}: {type(payload)!r}")
        return payload

    def _request_json_impl(
        self, path: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        response = self._get_session().get(
            self._build_api_url(path),
            params=params,
            timeout=30,
        )
        if response.status_code == 401:
            raise PermissionError("GitHub API rejected the provided PAT.")
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise ValueError(f"Unexpected payload type for {path}: {type(payload)!r}")
        return payload

    def _request_all(
        self, path: str, params: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve all pages for a list-based GitHub API endpoint."""

        results: List[Dict[str, Any]] = []
        base_params: Dict[str, Any] = dict(params or {})
        per_page = int(base_params.get("per_page") or 100)
        page = 1

        while True:
            page_params = base_params | {"page": page, "per_page": per_page}
            data = self._request(path, page_params)
            if not data:
                break
            results.extend(data)
            if len(data) < per_page:
                break
            page += 1

        return results

    def _paginate(
        self,
        path: str,
        base_params: Dict[str, Any],
        per_page: int = 100,
        early_stop: Optional[Callable[[Dict[str, Any]], bool]] = None,
    ) -> List[Dict[str, Any]]:
        """Generic pagination helper with optional early stopping.

        Args:
            path: API endpoint path
            base_params: Base query parameters
            per_page: Items per page (default: 100)
            early_stop: Optional callback that receives each item and returns True to stop pagination

        Returns:
            List of collected items
        """
        results: List[Dict[str, Any]] = []
        page = 1

        while True:
            page_params = base_params | {"page": page, "per_page": per_page}
            data = self._request(path, page_params)

            if not data:
                break

            # Check early stop condition for each item
            if early_stop:
                for item in data:
                    if early_stop(item):
                        return results
                    results.append(item)
            else:
                results.extend(data)

            if len(data) < per_page:
                break

            page += 1

        return results

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
        seen_shas: Set[str] = set()
        include_branches: Sequence[Optional[str]]
        exclude_branches = set(filters.exclude_branches)
        if filters.include_branches:
            include_branches = [
                branch
                for branch in filters.include_branches
                if branch not in exclude_branches
            ]
        elif exclude_branches:
            branches = self._request_all(
                f"repos/{repo}/branches",
                {"per_page": 100},
            )
            include_branches = [
                branch.get("name")
                for branch in branches
                if branch.get("name") and branch.get("name") not in exclude_branches
            ]
        else:
            include_branches = [None]

        if not include_branches:
            return 0

        path_filters = filters.include_paths or [None]
        commit_file_cache: Dict[str, List[str]] = {}

        for branch in include_branches:
            for path_filter in path_filters:
                page = 1
                base_params: Dict[str, Any] = {
                    "since": since.isoformat(),
                    "per_page": 100,
                }
                if branch:
                    base_params["sha"] = branch
                if path_filter:
                    base_params["path"] = path_filter

                while True:
                    page_params = base_params | {"page": page}
                    data = self._request(f"repos/{repo}/commits", page_params)
                    if not data:
                        break
                    for commit in data:
                        author = commit.get("author")
                        if self._filter_bot(author, filters):
                            continue
                        sha = commit.get("sha")
                        if not sha or sha in seen_shas:
                            continue
                        if not self._commit_matches_path_filters(
                            repo, sha, filters, commit_file_cache
                        ):
                            continue
                        seen_shas.add(sha)
                        total += 1
                    if len(data) < 100:
                        break
                    page += 1
        return total

    def _list_pull_requests(
        self, repo: str, since: datetime, filters: AnalysisFilters
    ) -> tuple[int, List[Dict[str, Any]]]:
        params: Dict[str, Any] = {
            "state": "all",
            "per_page": 100,
            "sort": "created",
            "direction": "desc",
        }

        pr_file_cache: Dict[int, List[Dict[str, Any]]] = {}

        def should_stop(pr: Dict[str, Any]) -> bool:
            """Early stop condition: PR created before analysis period."""
            created_at = self._parse_timestamp(pr["created_at"]).astimezone(timezone.utc)
            return created_at < since

        all_prs = self._paginate(
            f"repos/{repo}/pulls",
            base_params=params,
            per_page=100,
            early_stop=should_stop,
        )

        # Apply filters
        metadata: List[Dict[str, Any]] = []
        for pr in all_prs:
            author = pr.get("user")
            if self._filter_bot(author, filters):
                continue
            if not self._pr_matches_branch_filters(pr, filters):
                continue
            if not self._pr_matches_file_filters(repo, pr, filters, pr_file_cache):
                continue
            metadata.append(pr)

        return len(metadata), metadata

    def _build_pull_request_examples(
        self, pr_metadata: List[Dict[str, Any]]
    ) -> List[PullRequestSummary]:
        """Transform raw pull request metadata into reporting friendly examples."""

        examples: List[PullRequestSummary] = []
        for pr in pr_metadata[:5]:
            author = pr.get("user") or {}
            merged_at_raw = pr.get("merged_at")
            merged_at = (
                self._parse_timestamp(merged_at_raw).astimezone(timezone.utc)
                if merged_at_raw
                else None
            )
            created_at = self._parse_timestamp(pr["created_at"]).astimezone(timezone.utc)
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

    def _count_reviews(
        self,
        repo: str,
        pull_requests: Iterable[Dict[str, Any]],
        since: datetime,
        filters: AnalysisFilters,
    ) -> int:
        from concurrent.futures import ThreadPoolExecutor, as_completed

        pr_file_cache: Dict[int, List[Dict[str, Any]]] = {}
        valid_prs = []

        # Filter PRs first
        for pr in pull_requests:
            if not self._pr_matches_branch_filters(pr, filters):
                continue
            if not self._pr_matches_file_filters(repo, pr, filters, pr_file_cache):
                continue
            valid_prs.append(pr)

        # Parallelize review fetching
        def fetch_pr_reviews(pr: Dict[str, Any]) -> int:
            number = pr["number"]
            count = 0

            # Fetch all reviews for this PR using paginate
            all_reviews = self._paginate(
                f"repos/{repo}/pulls/{number}/reviews",
                base_params={"per_page": 100},
                per_page=100,
            )

            # Count reviews that pass filters
            for review in all_reviews:
                submitted_at = review.get("submitted_at")
                if submitted_at:
                    submitted_dt = self._parse_timestamp(submitted_at).astimezone(timezone.utc)
                    if submitted_dt < since:
                        continue
                author = review.get("user")
                if self._filter_bot(author, filters):
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
                        console.log(f"Review counting progress: {completed_count}/{total_prs} PRs processed")
                except requests.HTTPError as exc:
                    logger.warning(f"Failed to fetch reviews for PR #{pr_num}: HTTP {exc.response.status_code if exc.response else 'error'}")
                except Exception as exc:
                    logger.warning(f"Failed to fetch reviews for PR #{pr_num}: {exc}")

        return total

    def _count_issues(
        self, repo: str, since: datetime, filters: AnalysisFilters
    ) -> int:
        params: Dict[str, Any] = {
            "state": "all",
            "per_page": 100,
            "since": since.isoformat(),
        }

        all_issues = self._paginate(f"repos/{repo}/issues", base_params=params, per_page=100)

        # Count issues that pass filters
        total = 0
        for issue in all_issues:
            if "pull_request" in issue:
                continue
            author = issue.get("user")
            if self._filter_bot(author, filters):
                continue
            if not self._issue_matches_filters(issue, filters):
                continue
            total += 1

        return total

    # Filtering helpers -------------------------------------------------

    def _apply_file_filters(
        self,
        filenames: List[str],
        filters: AnalysisFilters,
    ) -> bool:
        """Apply path and language filters to a list of filenames.

        Args:
            filenames: List of file paths to check
            filters: Analysis filters to apply

        Returns:
            True if filenames pass all filters, False otherwise
        """
        if not filters.include_paths and not filters.exclude_paths and not filters.include_languages:
            return True

        # Check include_paths filter
        if filters.include_paths:
            if not any(
                self._path_matches(filename, include_path)
                for filename in filenames
                for include_path in filters.include_paths
            ):
                return False

        # Check exclude_paths filter
        if filters.exclude_paths:
            if any(
                self._path_matches(filename, exclude_path)
                for filename in filenames
                for exclude_path in filters.exclude_paths
            ):
                return False

        # Check include_languages filter
        if filters.include_languages:
            include_languages_normalised = self._normalise_language_filters(
                filters.include_languages
            )
            if include_languages_normalised:
                file_language_tokens = {
                    token
                    for filename in filenames
                    for token in self._filename_language_tokens(filename)
                }
                if not file_language_tokens.intersection(include_languages_normalised):
                    return False

        return True

    def _commit_matches_path_filters(
        self,
        repo: str,
        sha: str,
        filters: AnalysisFilters,
        cache: Dict[str, List[str]],
    ) -> bool:
        # Get files from cache or fetch from API
        files = cache.get(sha)
        if files is None:
            payload = self._request_json(f"repos/{repo}/commits/{sha}")
            file_entries = payload.get("files") or []
            files = [entry.get("filename", "") for entry in file_entries]
            cache[sha] = files

        return self._apply_file_filters(files, filters)

    @staticmethod
    def _path_matches(path: str, prefix: str) -> bool:
        if not prefix:
            return True
        return path.startswith(prefix)

    def _pr_matches_branch_filters(
        self, pr: Dict[str, Any], filters: AnalysisFilters
    ) -> bool:
        include = filters.include_branches
        exclude = set(filters.exclude_branches)
        base_ref = ((pr.get("base") or {}).get("ref") or "")
        head_ref = ((pr.get("head") or {}).get("ref") or "")

        if base_ref in exclude or head_ref in exclude:
            return False
        if include:
            return base_ref in include or head_ref in include
        return True

    def _pr_matches_file_filters(
        self,
        repo: str,
        pr: Dict[str, Any],
        filters: AnalysisFilters,
        cache: Dict[int, List[Dict[str, Any]]],
    ) -> bool:
        # Get PR files from cache or fetch from API
        number = int(pr.get("number", 0))
        files = cache.get(number)
        if files is None:
            files = self._request_all(
                f"repos/{repo}/pulls/{number}/files", {"per_page": 100}
            )
            cache[number] = files

        filenames = [entry.get("filename", "") for entry in files]
        return self._apply_file_filters(filenames, filters)

    @staticmethod
    def _normalise_language_filters(include_languages: Sequence[str]) -> Set[str]:
        normalised: Set[str] = set()
        for value in include_languages:
            token = str(value or "").strip().lower()
            if not token:
                continue
            token = token.lstrip(".")
            if token:
                normalised.add(token)
        return normalised

    @staticmethod
    def _filename_language_tokens(filename: str) -> Set[str]:
        tokens: Set[str] = set()
        if "." not in filename:
            return tokens
        extension = filename.rsplit(".", 1)[-1].lower()
        if not extension:
            return tokens
        tokens.add(extension)
        language = LANGUAGE_EXTENSION_MAP.get(extension)
        if language:
            tokens.add(language.lower())
        return tokens

    @staticmethod
    def _filename_to_language(filename: str) -> Optional[str]:
        if "." not in filename:
            return None
        extension = filename.rsplit(".", 1)[-1].lower()
        if not extension:
            return None
        return LANGUAGE_EXTENSION_MAP.get(extension)

    def _issue_matches_filters(
        self, issue: Dict[str, Any], filters: AnalysisFilters
    ) -> bool:
        filenames = self._extract_issue_files(issue)
        return self._apply_file_filters(filenames, filters)

    @staticmethod
    def _extract_issue_files(issue: Dict[str, Any]) -> List[str]:
        files: List[str] = []
        issue_files = issue.get("files")
        if isinstance(issue_files, list):
            files.extend(str(filename) for filename in issue_files)
        labels = issue.get("labels") or []
        for label in labels:
            name = str((label or {}).get("name") or "")
            if name.startswith("path:"):
                files.append(name.split("path:", 1)[1])
            if name.startswith("file:"):
                files.append(name.split("file:", 1)[1])
        return files

    # Pull request review helpers --------------------------------------

    def get_authenticated_user(self) -> str:
        """Return the username of the authenticated user (PAT owner)."""
        user_data = self._request_json("user")
        username = user_data.get("login", "")
        if not username:
            raise ValueError("Failed to retrieve authenticated user from PAT")
        return username

    def list_authored_pull_requests(
        self, repo: str, author: str, state: str = "all"
    ) -> List[int]:
        """Return pull request numbers where the user is the author."""

        state_normalised = state.lower().strip() or "all"
        if state_normalised not in {"open", "closed", "all"}:
            raise ValueError(
                "state must be one of 'open', 'closed', or 'all'"
            )

        console.log(
            "Listing authored pull requests",
            f"repo={repo}",
            f"author={author}",
            f"state={state_normalised}",
        )

        params = {
            "creator": author,
            "state": state_normalised,
            "per_page": 100,
        }

        issues = self._request_all(f"repos/{repo}/issues", params)
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

    def collect_pull_request_details(

        self, repo: str, number: int
    ) -> PullRequestReviewBundle:
        """Gather detailed information for a single pull request."""

        console.log(
            "Collecting pull request artefacts",
            f"repo={repo}",
            f"number={number}",
        )

        pr_payload = self._request_json(f"repos/{repo}/pulls/{number}")
        review_payload = self._request_all(
            f"repos/{repo}/pulls/{number}/reviews",
            {"per_page": 100},
        )
        review_comment_payload = self._request_all(
            f"repos/{repo}/pulls/{number}/comments",
            {"per_page": 100},
        )
        files_payload = self._request_all(
            f"repos/{repo}/pulls/{number}/files",
            {"per_page": 100},
        )

        created_at_raw = pr_payload.get("created_at", datetime.now(timezone.utc).isoformat())
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
            created_at=self._parse_timestamp(created_at_raw).astimezone(timezone.utc),
            updated_at=self._parse_timestamp(updated_at_raw).astimezone(timezone.utc),
            additions=int(pr_payload.get("additions", 0) or 0),
            deletions=int(pr_payload.get("deletions", 0) or 0),
            changed_files=int(pr_payload.get("changed_files", 0) or len(files)),
            review_bodies=review_bodies,
            review_comments=review_comments,
            files=files,
        )

    # Detailed feedback collection methods ---------------------------------

    def collect_commit_messages(
        self,
        repo: str,
        since: datetime,
        filters: Optional[AnalysisFilters] = None,
        limit: int = 100,
    ) -> List[Dict[str, str]]:
        """Collect commit messages for quality analysis."""
        filters = filters or AnalysisFilters()
        commits: List[Dict[str, str]] = []
        seen_shas: Set[str] = set()

        include_branches: Sequence[Optional[str]]
        exclude_branches = set(filters.exclude_branches)
        if filters.include_branches:
            include_branches = [
                branch
                for branch in filters.include_branches
                if branch not in exclude_branches
            ]
        elif exclude_branches:
            branches = self._request_all(
                f"repos/{repo}/branches",
                {"per_page": 100},
            )
            include_branches = [
                branch.get("name")
                for branch in branches
                if branch.get("name") and branch.get("name") not in exclude_branches
            ]
        else:
            include_branches = [None]

        if not include_branches:
            return []

        for branch in include_branches:
            if len(commits) >= limit:
                break

            params: Dict[str, Any] = {
                "since": since.isoformat(),
                "per_page": min(100, limit - len(commits)),
            }
            if branch:
                params["sha"] = branch

            data = self._request(f"repos/{repo}/commits", params)
            for item in data:
                sha = item.get("sha", "")
                if sha in seen_shas:
                    continue
                seen_shas.add(sha)

                author = item.get("author")
                if self._filter_bot(author, filters):
                    continue

                commit_data = item.get("commit", {})
                message = commit_data.get("message", "")
                commits.append({
                    "sha": sha,
                    "message": message,
                    "author": (commit_data.get("author") or {}).get("name", ""),
                    "date": commit_data.get("author", {}).get("date", ""),
                })

                if len(commits) >= limit:
                    break

        return commits[:limit]

    def collect_pr_titles(
        self,
        repo: str,
        since: datetime,
        filters: Optional[AnalysisFilters] = None,
        limit: int = 100,
    ) -> List[Dict[str, str]]:
        """Collect pull request titles for quality analysis."""
        filters = filters or AnalysisFilters()
        pr_titles: List[Dict[str, str]] = []

        params: Dict[str, Any] = {
            "state": "all",
            "sort": "created",
            "direction": "desc",
            "per_page": limit,
        }

        data = self._request(f"repos/{repo}/pulls", params)
        for pr in data:
            created_at_raw = pr.get("created_at")
            if not created_at_raw:
                continue

            created_at = self._parse_timestamp(created_at_raw).astimezone(timezone.utc)
            if created_at < since:
                continue

            author = pr.get("user")
            if self._filter_bot(author, filters):
                continue

            if not self._pr_matches_branch_filters(pr, filters):
                continue

            pr_titles.append({
                "number": pr.get("number", 0),
                "title": pr.get("title", ""),
                "author": (pr.get("user") or {}).get("login", ""),
                "url": pr.get("html_url", ""),
                "state": pr.get("state", ""),
            })

            if len(pr_titles) >= limit:
                break

        return pr_titles[:limit]

    def collect_review_comments_detailed(
        self,
        repo: str,
        since: datetime,
        filters: Optional[AnalysisFilters] = None,
        limit: int = 100,
    ) -> List[Dict[str, str]]:
        """Collect review comments for tone analysis."""
        filters = filters or AnalysisFilters()
        review_comments: List[Dict[str, str]] = []

        # Get pull requests first
        params: Dict[str, Any] = {
            "state": "all",
            "sort": "created",
            "direction": "desc",
            "per_page": 50,
        }

        prs = self._request(f"repos/{repo}/pulls", params)
        for pr in prs:
            if len(review_comments) >= limit:
                break

            created_at_raw = pr.get("created_at")
            if not created_at_raw:
                continue

            created_at = self._parse_timestamp(created_at_raw).astimezone(timezone.utc)
            if created_at < since:
                continue

            number = pr.get("number")
            if not number:
                continue

            # Get reviews for this PR
            try:
                reviews = self._request(
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
                    if self._filter_bot(review_author, filters):
                        continue

                    review_comments.append({
                        "pr_number": number,
                        "author": (review.get("user") or {}).get("login", ""),
                        "body": body,
                        "state": review.get("state", ""),
                        "submitted_at": review.get("submitted_at", ""),
                    })
            except Exception:
                # Skip PRs that fail to fetch reviews
                continue

        return review_comments[:limit]

    def collect_issue_details(
        self,
        repo: str,
        since: datetime,
        filters: Optional[AnalysisFilters] = None,
        limit: int = 100,
    ) -> List[Dict[str, str]]:
        """Collect issue details for quality analysis."""
        filters = filters or AnalysisFilters()
        issues: List[Dict[str, str]] = []

        params: Dict[str, Any] = {
            "state": "all",
            "sort": "created",
            "direction": "desc",
            "per_page": limit,
            "since": since.isoformat(),
        }

        data = self._request(f"repos/{repo}/issues", params)
        for issue in data:
            # Skip pull requests (GitHub API returns them as issues)
            if "pull_request" in issue:
                continue

            author = issue.get("user")
            if self._filter_bot(author, filters):
                continue

            issues.append({
                "number": issue.get("number", 0),
                "title": issue.get("title", ""),
                "body": issue.get("body", "") or "",
                "author": (issue.get("user") or {}).get("login", ""),
                "url": issue.get("html_url", ""),
                "state": issue.get("state", ""),
                "created_at": issue.get("created_at", ""),
            })

            if len(issues) >= limit:
                break

        return issues[:limit]

    # Year-end review specific collection methods ---------------------------------

    def collect_monthly_trends(
        self,
        repo: str,
        since: datetime,
        filters: Optional[AnalysisFilters] = None,
    ) -> List[Dict[str, Any]]:
        """Collect monthly activity trends for time-series analysis."""
        filters = filters or AnalysisFilters()

        # Initialize monthly buckets
        from collections import defaultdict
        monthly_data: Dict[str, Dict[str, int]] = defaultdict(
            lambda: {"commits": 0, "pull_requests": 0, "reviews": 0, "issues": 0}
        )

        # Collect commits by month
        seen_shas: Set[str] = set()
        include_branches: Sequence[Optional[str]] = [None]

        for branch in include_branches:
            params: Dict[str, Any] = {
                "since": since.isoformat(),
                "per_page": 100,
            }
            if branch:
                params["sha"] = branch

            try:
                commits = self._request_all(f"repos/{repo}/commits", params)
                for commit in commits:
                    sha = commit.get("sha", "")
                    if sha in seen_shas:
                        continue
                    seen_shas.add(sha)

                    author = commit.get("author")
                    if self._filter_bot(author, filters):
                        continue

                    commit_data = commit.get("commit", {})
                    date_str = commit_data.get("author", {}).get("date", "")
                    if date_str:
                        commit_date = self._parse_timestamp(date_str)
                        month_key = commit_date.strftime("%Y-%m")
                        monthly_data[month_key]["commits"] += 1
            except Exception:
                pass

        # Collect PRs by month
        try:
            params = {
                "state": "all",
                "sort": "created",
                "direction": "desc",
                "per_page": 100,
            }
            prs = self._request_all(f"repos/{repo}/pulls", params)
            for pr in prs:
                created_at_raw = pr.get("created_at")
                if not created_at_raw:
                    continue

                created_at = self._parse_timestamp(created_at_raw).astimezone(timezone.utc)
                if created_at < since:
                    continue

                author = pr.get("user")
                if self._filter_bot(author, filters):
                    continue

                month_key = created_at.strftime("%Y-%m")
                monthly_data[month_key]["pull_requests"] += 1
        except Exception:
            pass

        # Convert to list and sort by month
        result = []
        for month_key in sorted(monthly_data.keys()):
            result.append({
                "month": month_key,
                **monthly_data[month_key]
            })

        return result

    def collect_tech_stack(
        self,
        repo: str,
        pr_metadata: List[Dict[str, Any]],
    ) -> Dict[str, int]:
        """Analyze technology stack from PR file changes."""
        from concurrent.futures import ThreadPoolExecutor, as_completed

        language_counts: Dict[str, int] = {}

        def fetch_pr_files(pr: Dict[str, Any]) -> Dict[str, int]:
            """Fetch files for a single PR and count languages."""
            number = int(pr.get("number", 0))
            local_counts: Dict[str, int] = {}

            try:
                files = self._request_all(
                    f"repos/{repo}/pulls/{number}/files",
                    {"per_page": 100}
                )

                for file_entry in files:
                    filename = file_entry.get("filename", "")
                    language = self._filename_to_language(filename)
                    if language:
                        local_counts[language] = local_counts.get(language, 0) + 1

            except Exception:
                pass

            return local_counts

        # Parallelize file fetching for recent 50 PRs
        prs_to_process = pr_metadata[:50]
        completed_count = 0
        total_prs = len(prs_to_process)

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {
                executor.submit(fetch_pr_files, pr): pr
                for pr in prs_to_process
            }

            for future in as_completed(futures):
                completed_count += 1
                try:
                    local_counts = future.result()
                    for language, count in local_counts.items():
                        language_counts[language] = language_counts.get(language, 0) + count
                    if completed_count % 10 == 0 or completed_count == total_prs:
                        console.log(f"Tech stack analysis progress: {completed_count}/{total_prs} PRs analyzed")
                except Exception:
                    continue

        return language_counts

    def collect_collaboration_network(
        self,
        repo: str,
        pr_metadata: List[Dict[str, Any]],
        filters: Optional[AnalysisFilters] = None,
    ) -> Dict[str, Any]:
        """Analyze collaboration patterns from PR reviews."""
        from concurrent.futures import ThreadPoolExecutor, as_completed

        filters = filters or AnalysisFilters()
        reviewer_counts: Dict[str, int] = {}
        total_reviews_received = 0
        unique_reviewers: Set[str] = set()

        def fetch_pr_reviews(pr: Dict[str, Any]) -> tuple[Dict[str, int], Set[str], int]:
            """Fetch reviews for a single PR and count reviewers."""
            number = pr["number"]
            local_counts: Dict[str, int] = {}
            local_reviewers: Set[str] = set()
            local_total = 0

            try:
                reviews = self._request_all(
                    f"repos/{repo}/pulls/{number}/reviews",
                    {"per_page": 100}
                )

                for review in reviews:
                    reviewer = review.get("user")
                    if self._filter_bot(reviewer, filters):
                        continue

                    reviewer_login = (reviewer or {}).get("login", "")
                    if not reviewer_login:
                        continue

                    local_counts[reviewer_login] = local_counts.get(reviewer_login, 0) + 1
                    local_reviewers.add(reviewer_login)
                    local_total += 1
            except Exception:
                pass

            return local_counts, local_reviewers, local_total

        # Parallelize review fetching for recent 100 PRs
        prs_to_process = pr_metadata[:100]
        completed_count = 0
        total_prs = len(prs_to_process)

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {
                executor.submit(fetch_pr_reviews, pr): pr
                for pr in prs_to_process
            }

            for future in as_completed(futures):
                completed_count += 1
                try:
                    local_counts, local_reviewers, local_total = future.result()
                    for reviewer, count in local_counts.items():
                        reviewer_counts[reviewer] = reviewer_counts.get(reviewer, 0) + count
                    unique_reviewers.update(local_reviewers)
                    total_reviews_received += local_total
                    if completed_count % 20 == 0 or completed_count == total_prs:
                        console.log(f"Collaboration network progress: {completed_count}/{total_prs} PRs analyzed")
                except Exception:
                    continue

        return {
            "pr_reviewers": reviewer_counts,
            "review_received_count": total_reviews_received,
            "unique_collaborators": len(unique_reviewers),
        }
