"""Builders for various metrics and summaries."""

from __future__ import annotations

from typing import Dict, List, TYPE_CHECKING

if TYPE_CHECKING:
    from github_feedback.core.models import CollectionResult

from github_feedback.core.constants import COLLECTION_LIMITS
from github_feedback.analyzer.helpers import PeriodFormatter


class HighlightsBuilder:
    """Build activity highlights."""

    @staticmethod
    def build(
        collection: CollectionResult,
        period_label: str,
        month_span: int,
        velocity_score: float,
        total_activity: int,
    ) -> List[str]:
        """Build activity highlights from collection data."""
        highlights: List[str] = []
        if collection.commits:
            highlights.append(
                f"{period_label}에 총 {collection.commits}회의 커밋으로 코드를 다듬고 월 평균 {velocity_score:.1f}회의 개선을 이어갔습니다."
            )
        if collection.pull_requests:
            highlights.append(
                f"{collection.pull_requests}건의 Pull Request를 병합하며 팀 배포 주기를 안정화했고 월 {collection.pull_requests / month_span:.1f}건의 릴리스를 유지했습니다."
            )
        if collection.reviews:
            highlights.append(
                f"{collection.reviews}회의 코드 리뷰를 통해 협업 문화를 강화했습니다."
            )
        if collection.issues:
            highlights.append(
                f"활동 대비 {collection.issues}건의 이슈로 안정성을 지켰습니다."
            )
        if not highlights and total_activity == 0:
            highlights.append("분석 기간 동안 뚜렷한 활동이 감지되지 않았습니다.")

        return highlights


class SpotlightExamplesBuilder:
    """Build spotlight PR examples."""

    def __init__(self, web_base_url: str = "https://github.com"):
        """Initialize with web base URL."""
        self.web_base_url = web_base_url

    def build(self, collection: CollectionResult) -> Dict[str, List[str]]:
        """Build spotlight examples from collection data."""
        spotlight_examples: Dict[str, List[str]] = {}
        if not collection.pull_request_examples:
            return spotlight_examples

        pr_lines = []
        for pr in collection.pull_request_examples[:COLLECTION_LIMITS['pr_examples']]:
            change_volume = pr.additions + pr.deletions
            scale_phrase = f"변경 {change_volume}줄" if change_volume else "경량 변경"
            merged_phrase = (
                f"{pr.merged_at.date().isoformat()} 병합"
                if pr.merged_at
                else "미병합"
            )
            pr_lines.append(
                f"PR #{pr.number} · {pr.title} — {pr.author} ({pr.created_at.date().isoformat()}, {merged_phrase}, {scale_phrase}) · {pr.html_url}"
            )
        spotlight_examples["pull_requests"] = pr_lines
        return spotlight_examples


class SummaryBuilder:
    """Build summary statistics."""

    @staticmethod
    def build(
        period_label: str,
        total_activity: int,
        velocity_score: float,
        collaboration_score: float,
        stability_score: int,
    ) -> Dict[str, str]:
        """Build summary dictionary."""
        return {
            "velocity": f"Average {velocity_score:.1f} commits per month",
            "collaboration": "{:.1f} combined PRs and reviews per month".format(collaboration_score),
            "stability": f"Net stability score of {stability_score}",
            "growth": f"{period_label} 동안 {total_activity}건의 활동을 기록했습니다.",
        }


class StoryBeatsBuilder:
    """Build story beats narrative."""

    @staticmethod
    def build(
        collection: CollectionResult,
        period_label: str,
        total_activity: int,
    ) -> List[str]:
        """Build story beats from collection data."""
        story_beats: List[str] = []
        if total_activity:
            story_beats.append(
                f"{period_label} 동안 {collection.repo} 저장소에서 총 {total_activity}건의 활동을 펼치며 성장 엔진을 가동했습니다."
            )
        else:
            story_beats.append(
                f"{period_label}에는 잠시 숨을 고르며 다음 도약을 준비했습니다."
            )

        contribution_domains = [
            ("커밋", collection.commits, "지속적인 리팩터링과 기능 확장을 이끌었습니다."),
            ("Pull Request", collection.pull_requests, "협업 릴리스를 주도하며 배포 파이프라인을 지켰습니다."),
            ("리뷰", collection.reviews, "팀 동료들의 성장을 돕는 촘촘한 피드백을 전달했습니다."),
        ]
        top_domain = max(contribution_domains, key=lambda entry: entry[1])
        if top_domain[1]:
            story_beats.append(
                f"가장 눈에 띈 영역은 {top_domain[0]} {top_domain[1]}회로, {top_domain[2]}"
            )

        if collection.pull_request_examples:
            exemplar = collection.pull_request_examples[0]
            merge_phrase = (
                f"{exemplar.merged_at.date().isoformat()} 병합"
                if exemplar.merged_at
                else "아직 진행 중"
            )
            scale = exemplar.additions + exemplar.deletions
            scale_phrase = f"변경 {scale}줄" if scale else "경량 변경"
            story_beats.append(
                "대표작으로는 PR #{num} `{title}`({author})가 있습니다 — {created} 작성, {merge} · {scale_phrase}.".format(
                    num=exemplar.number,
                    title=exemplar.title,
                    author=exemplar.author,
                    created=exemplar.created_at.date().isoformat(),
                    merge=merge_phrase,
                    scale_phrase=scale_phrase,
                )
            )

        return story_beats


class StatsBuilder:
    """Build statistics dictionary."""

    @staticmethod
    def build(collection: CollectionResult, velocity_score: float) -> Dict[str, Dict[str, float]]:
        """Build stats dictionary from collection data."""
        return {
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


class EvidenceBuilder:
    """Build evidence links."""

    def __init__(self, web_base_url: str = "https://github.com"):
        """Initialize with web base URL."""
        self.web_base_url = web_base_url

    def build(self, collection: CollectionResult) -> Dict[str, List[str]]:
        """Build evidence links from collection data."""
        repo_root = f"{self.web_base_url.rstrip('/')}/{collection.repo}"
        return {
            "commits": [
                f"{repo_root}/commits",
            ],
            "pull_requests": [
                f"{repo_root}/pulls",
            ],
        }
