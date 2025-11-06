"""Metric calculation logic for GitHub feedback analysis."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict

from .console import Console
from .models import AnalysisStatus, CollectionResult, MetricSnapshot

console = Console()


@dataclass(slots=True)
class Analyzer:
    """Transform collected data into actionable metrics."""

    web_base_url: str = "https://github.com"

    def compute_metrics(self, collection: CollectionResult) -> MetricSnapshot:
        """Compute derived metrics from the collected artefacts."""

        console.log("Analyzing repository trends", repo=collection.repo)

        velocity_score = collection.commits / max(collection.months, 1)
        collaboration_score = (
            (collection.pull_requests + collection.reviews) / max(collection.months, 1)
        )
        stability_score = max(collection.commits - collection.issues, 0)

        summary = {
            "velocity": f"Average {velocity_score:.1f} commits per month",
            "collaboration": (
                "{:.1f} combined PRs and reviews per month".format(collaboration_score)
            ),
            "stability": f"Net stability score of {stability_score}",
        }

        stats: Dict[str, Dict[str, float]] = {
            "commits": {
                "total": float(collection.commits),
                "per_month": velocity_score,
            },
            "pull_requests": {
                "total": float(collection.pull_requests),
            },
            "reviews": {
                "total": float(collection.reviews),
            },
            "issues": {
                "total": float(collection.issues),
            },
        }

        repo_root = f"{self.web_base_url.rstrip('/')}/{collection.repo}"
        evidence = {
            "commits": [
                f"{repo_root}/commits",
            ],
            "pull_requests": [
                f"{repo_root}/pulls",
            ],
        }

        return MetricSnapshot(
            repo=collection.repo,
            months=collection.months,
            generated_at=datetime.utcnow(),
            status=AnalysisStatus.ANALYSED,
            summary=summary,
            stats=stats,
            evidence=evidence,
        )
