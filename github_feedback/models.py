"""Domain models shared across the GitHub feedback toolkit."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional


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
