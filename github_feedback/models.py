"""Domain models shared across the GitHub feedback toolkit."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional


@dataclass(slots=True)
class ReviewPoint:
    """Single highlight used when summarising pull requests."""

    message: str
    example: Optional[str] = None

    def to_dict(self) -> Dict[str, Optional[str]]:
        """Serialise the review point for JSON persistence."""

        payload: Dict[str, Optional[str]] = {"message": self.message}
        if self.example:
            payload["example"] = self.example
        return payload


@dataclass(slots=True)
class ReviewSummary:
    """Structured response returned from LLM powered reviews."""

    overview: str
    strengths: List[ReviewPoint] = field(default_factory=list)
    improvements: List[ReviewPoint] = field(default_factory=list)

    def to_dict(self) -> Dict[str, object]:
        """Convert the summary into a JSON friendly payload."""

        return {
            "overview": self.overview,
            "strengths": [point.to_dict() for point in self.strengths],
            "improvements": [point.to_dict() for point in self.improvements],
        }


@dataclass(slots=True)
class PullRequestFile:
    """Individual file diff captured when reviewing a pull request."""

    filename: str
    status: str
    additions: int
    deletions: int
    changes: int
    patch: Optional[str] = None

    def to_dict(self) -> Dict[str, object]:
        """Serialise the file metadata for persistence."""

        payload: Dict[str, object] = {
            "filename": self.filename,
            "status": self.status,
            "additions": self.additions,
            "deletions": self.deletions,
            "changes": self.changes,
        }
        if self.patch is not None:
            payload["patch"] = self.patch
        return payload


@dataclass(slots=True)
class PullRequestReviewBundle:
    """Complete snapshot of a pull request for LLM reviews."""

    repo: str
    number: int
    title: str
    body: str
    author: str
    html_url: str
    created_at: datetime
    updated_at: datetime
    additions: int
    deletions: int
    changed_files: int
    review_bodies: List[str]
    review_comments: List[str]
    files: List[PullRequestFile]

    def to_dict(self) -> Dict[str, object]:
        """Convert the bundle into a JSON serialisable structure."""

        return {
            "repo": self.repo,
            "number": self.number,
            "title": self.title,
            "body": self.body,
            "author": self.author,
            "html_url": self.html_url,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "additions": self.additions,
            "deletions": self.deletions,
            "changed_files": self.changed_files,
            "review_bodies": self.review_bodies,
            "review_comments": self.review_comments,
            "files": [file.to_dict() for file in self.files],
        }


class AnalysisStatus(str, Enum):
    """Lifecycle marker for analysis runs."""

    CREATED = "created"
    COLLECTED = "collected"
    ANALYSED = "analysed"
    REPORTED = "reported"


@dataclass(slots=True)
class AnalysisFilters:
    """Filters controlling which repository artefacts are collected."""

    include_branches: List[str] = field(default_factory=list)
    exclude_branches: List[str] = field(default_factory=list)
    include_paths: List[str] = field(default_factory=list)
    exclude_paths: List[str] = field(default_factory=list)
    include_languages: List[str] = field(default_factory=list)
    exclude_bots: bool = True


@dataclass(slots=True)
class CollectionResult:
    """Summary of the raw artefacts collected from GitHub."""

    repo: str
    months: int
    collected_at: datetime
    commits: int
    pull_requests: int
    reviews: int
    issues: int
    filters: AnalysisFilters


@dataclass(slots=True)
class MetricSnapshot:
    """Computed metrics ready for reporting."""

    repo: str
    months: int
    generated_at: datetime
    status: AnalysisStatus
    summary: Dict[str, str]
    stats: Dict[str, Dict[str, float]]
    evidence: Dict[str, List[str]]
