"""Data loading and parsing for review reports."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import List

from ..console import Console
from ..models import ReviewPoint

console = Console()


@dataclass(slots=True)
class StoredReview:
    """Stored review summary reconstructed from cached artefacts."""

    number: int
    title: str
    author: str
    html_url: str
    created_at: datetime
    overview: str
    strengths: List[ReviewPoint]
    improvements: List[ReviewPoint]
    body: str = ""
    review_bodies: List[str] | None = None
    review_comments: List[str] | None = None
    additions: int = 0
    deletions: int = 0
    changed_files: int = 0


class ReviewDataLoader:
    """Load and parse review data from cached artefacts."""

    def __init__(self, output_dir: Path = Path("reports/reviews")) -> None:
        self.output_dir = output_dir

    def _repo_dir(self, repo: str) -> Path:
        safe_repo = repo.replace("/", "__")
        return self.output_dir / safe_repo

    @staticmethod
    def _load_points(raw_points) -> List[ReviewPoint]:
        """Parse review points from raw data."""
        points: List[ReviewPoint] = []
        if not isinstance(raw_points, list):
            return points

        for payload in raw_points:
            if not isinstance(payload, dict):
                continue
            message = str(payload.get("message") or "").strip()
            if not message:
                continue
            example_raw = payload.get("example")
            example = str(example_raw).strip() if example_raw else None
            points.append(ReviewPoint(message=message, example=example))
        return points

    def load_reviews(self, repo: str) -> List[StoredReview]:
        """Load all reviews for a repository."""
        repo_dir = self._repo_dir(repo)
        if not repo_dir.exists():
            return []

        reviews: List[StoredReview] = []
        for pr_dir in sorted(repo_dir.glob("pr-*")):
            summary_data = self._load_json_payload(pr_dir / "review_summary.json")
            artefact_data = self._load_json_payload(pr_dir / "artefacts.json")
            if not summary_data or not artefact_data:
                continue

            stored_review = self._build_stored_review(summary_data, artefact_data, pr_dir)
            if stored_review:
                reviews.append(stored_review)

        reviews.sort(key=lambda item: (item.created_at, item.number))
        return reviews

    def _load_json_payload(self, path: Path) -> dict | None:
        """Load and validate JSON payload from file."""
        if not path.exists():
            return None

        try:
            text = path.read_text(encoding="utf-8").strip()
        except OSError:
            console.log("Skipping unreadable artefact", str(path))
            return None

        if not text:
            console.log("Skipping empty review artefact", str(path.parent))
            return None

        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            console.log("Skipping invalid review artefact", str(path.parent))
            return None

        if not isinstance(payload, dict):
            console.log("Skipping unexpected review artefact", str(path.parent))
            return None

        return payload

    def _build_stored_review(
        self, summary_data: dict, artefact_data: dict, pr_dir: Path
    ) -> StoredReview | None:
        """Build StoredReview from summary and artefact data."""
        try:
            number = int(artefact_data.get("number"))
            title = str(artefact_data.get("title") or "").strip()
            author = str(artefact_data.get("author") or "unknown").strip()
            html_url = str(artefact_data.get("html_url") or "").strip()
            created_at_raw = artefact_data.get("created_at")
            created_at = (
                datetime.fromisoformat(created_at_raw)
                if isinstance(created_at_raw, str)
                else datetime.now(timezone.utc)
            )
        except Exception:  # pragma: no cover - defensive parsing guard
            console.log("Skipping malformed artefact", str(pr_dir))
            return None

        overview = str(summary_data.get("overview") or "").strip()
        strengths = self._load_points(summary_data.get("strengths", []))
        improvements = self._load_points(summary_data.get("improvements", []))

        body = str(artefact_data.get("body") or "").strip()
        review_bodies = artefact_data.get("review_bodies", [])
        review_comments = artefact_data.get("review_comments", [])
        additions = int(artefact_data.get("additions", 0))
        deletions = int(artefact_data.get("deletions", 0))
        changed_files = int(artefact_data.get("changed_files", 0))

        return StoredReview(
            number=number,
            title=title,
            author=author,
            html_url=html_url,
            created_at=created_at,
            overview=overview,
            strengths=strengths,
            improvements=improvements,
            body=body,
            review_bodies=review_bodies if isinstance(review_bodies, list) else [],
            review_comments=review_comments if isinstance(review_comments, list) else [],
            additions=additions,
            deletions=deletions,
            changed_files=changed_files,
        )


__all__ = ["StoredReview", "ReviewDataLoader"]
