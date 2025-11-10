"""GitHub data collection layer."""

from __future__ import annotations

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
        if self.config.auth is None or not self.config.auth.pat:
            raise ValueError("Authentication PAT is not configured. Run `gf init` first.")

        self._headers = {
            "Authorization": f"Bearer {self.config.auth.pat}",
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
            collected_at=datetime.utcnow(),
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
        else:
            include_branches = [None]

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
        pr_file_cache: Dict[int, List[Dict[str, Any]]] = {}
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
                if not self._pr_matches_branch_filters(pr, filters):
                    continue
                if not self._pr_matches_file_filters(
                    repo, pr, filters, pr_file_cache
                ):
                    continue
                total += 1
                metadata.append(pr)
            if len(data) < 100:
                break
            page += 1
        return total, metadata

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
        total = 0
        pr_file_cache: Dict[int, List[Dict[str, Any]]] = {}
        for pr in pull_requests:
            number = pr["number"]
            if not self._pr_matches_branch_filters(pr, filters):
                continue
            if not self._pr_matches_file_filters(repo, pr, filters, pr_file_cache):
                continue
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
                if not self._issue_matches_filters(issue, filters):
                    continue
                total += 1
            if len(data) < 100:
                break
            page += 1
        return total

    # Filtering helpers -------------------------------------------------

    def _commit_matches_path_filters(
        self,
        repo: str,
        sha: str,
        filters: AnalysisFilters,
        cache: Dict[str, List[str]],
    ) -> bool:
        if (
            not filters.include_paths
            and not filters.exclude_paths
            and not filters.include_languages
        ):
            return True
        files = cache.get(sha)
        if files is None:
            payload = self._request_json(f"repos/{repo}/commits/{sha}")
            file_entries = payload.get("files") or []
            files = [entry.get("filename", "") for entry in file_entries]
            cache[sha] = files

        if filters.include_paths:
            if not any(
                self._path_matches(path, include_path)
                for path in files
                for include_path in filters.include_paths
            ):
                return False
        if filters.exclude_paths:
            if any(
                self._path_matches(path, exclude_path)
                for path in files
                for exclude_path in filters.exclude_paths
            ):
                return False
        if filters.include_languages:
            include_languages_normalised = self._normalise_language_filters(
                filters.include_languages
            )
            if include_languages_normalised:
                file_language_tokens = {
                    token
                    for path in files
                    for token in self._filename_language_tokens(path)
                }
                if not file_language_tokens.intersection(include_languages_normalised):
                    return False
        return True

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
        if (
            not filters.include_paths
            and not filters.exclude_paths
            and not filters.include_languages
        ):
            return True

        number = int(pr.get("number", 0))
        files = cache.get(number)
        if files is None:
            files = self._request_all(
                f"repos/{repo}/pulls/{number}/files", {"per_page": 100}
            )
            cache[number] = files

        filenames = [entry.get("filename", "") for entry in files]

        if filters.include_paths:
            if not any(
                self._path_matches(filename, include_path)
                for filename in filenames
                for include_path in filters.include_paths
            ):
                return False
        if filters.exclude_paths:
            if any(
                self._path_matches(filename, exclude_path)
                for filename in filenames
                for exclude_path in filters.exclude_paths
            ):
                return False

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
        if (
            not filters.include_paths
            and not filters.exclude_paths
            and not filters.include_languages
        ):
            return True

        filenames = self._extract_issue_files(issue)
        if filters.include_paths:
            if not any(
                self._path_matches(filename, include_path)
                for filename in filenames
                for include_path in filters.include_paths
            ):
                return False
        if filters.exclude_paths:
            if any(
                self._path_matches(filename, exclude_path)
                for filename in filenames
                for exclude_path in filters.exclude_paths
            ):
                return False
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

    def list_assigned_pull_requests(
        self, repo: str, assignee: str, state: str = "all"
    ) -> List[int]:
        """Return pull request numbers where the user is an assignee."""

        state_normalised = state.lower().strip() or "all"
        if state_normalised not in {"open", "closed", "all"}:
            raise ValueError(
                "state must be one of 'open', 'closed', or 'all'"
            )

        console.log(
            "Listing assigned pull requests",
            f"repo={repo}",
            f"assignee={assignee}",
            f"state={state_normalised}",
        )

        params = {
            "assignee": assignee,
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

        created_at_raw = pr_payload.get("created_at", datetime.utcnow().isoformat())
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
