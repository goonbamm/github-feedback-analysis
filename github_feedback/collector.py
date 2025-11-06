"""GitHub data collection layer."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from .config import Config
from .console import Console
from .models import AnalysisFilters, CollectionResult

console = Console()


@dataclass(slots=True)
class Collector:
    """High-level wrapper around GitHub API collection."""

    config: Config

    def collect(
        self,
        repo: str,
        months: int,
        filters: Optional[AnalysisFilters] = None,
    ) -> CollectionResult:
        """Collect repository artefacts.

        This implementation is intentionally lightweight and focuses on plumbing.
        Actual API interactions will be added in future iterations. For now, the
        collector returns a deterministic stub dataset so that the rest of the
        pipeline can be exercised and tested end-to-end.
        """

        filters = filters or AnalysisFilters()

        console.log(
            "Collecting GitHub data", repo=repo, months=months
        )

        # Deterministic pseudo metrics derived from the repository name.
        base_value = sum(ord(char) for char in repo) % 100
        commits = base_value * months // 3 + 20
        pull_requests = max(base_value // 2, 5)
        reviews = max(base_value // 3, 3)
        issues = base_value // 4

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
