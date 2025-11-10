"""Metric calculation logic for GitHub feedback analysis."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List

from .console import Console
from .models import AnalysisStatus, CollectionResult, MetricSnapshot

console = Console()


@dataclass(slots=True)
class Analyzer:
    """Transform collected data into actionable metrics."""

    web_base_url: str = "https://github.com"

    def compute_metrics(self, collection: CollectionResult) -> MetricSnapshot:
        """Compute derived metrics from the collected artefacts."""

        console.log("Analyzing repository trends", f"repo={collection.repo}")

        (
            month_span,
            velocity_score,
            collaboration_score,
            stability_score,
            total_activity,
            period_label,
        ) = self._calculate_scores(collection)

        highlights = self._build_highlights(
            collection,
            period_label,
            month_span,
            velocity_score,
            total_activity,
        )
        spotlight_examples = self._build_spotlight_examples(collection)
        summary = self._build_summary(
            period_label,
            total_activity,
            velocity_score,
            collaboration_score,
            stability_score,
        )
        story_beats = self._build_story_beats(collection, period_label, total_activity)
        awards = self._determine_awards(collection)
        stats = self._build_stats(collection, velocity_score)
        evidence = self._build_evidence(collection)

        return MetricSnapshot(
            repo=collection.repo,
            months=collection.months,
            generated_at=datetime.utcnow(),
            status=AnalysisStatus.ANALYSED,
            summary=summary,
            stats=stats,
            evidence=evidence,
            highlights=highlights,
            spotlight_examples=spotlight_examples,
            yearbook_story=story_beats,
            awards=awards,
        )

    def _calculate_scores(
        self, collection: CollectionResult
    ) -> tuple[int, float, float, int, int, str]:
        month_span = max(collection.months, 1)
        velocity_score = collection.commits / month_span
        collaboration_score = (collection.pull_requests + collection.reviews) / month_span
        stability_score = max(collection.commits - collection.issues, 0)
        total_activity = collection.commits + collection.pull_requests + collection.reviews
        period_label = "올해" if collection.months >= 12 else f"지난 {collection.months}개월"

        return (
            month_span,
            velocity_score,
            collaboration_score,
            stability_score,
            total_activity,
            period_label,
        )

    def _build_highlights(
        self,
        collection: CollectionResult,
        period_label: str,
        month_span: int,
        velocity_score: float,
        total_activity: int,
    ) -> List[str]:
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

    def _build_spotlight_examples(self, collection: CollectionResult) -> Dict[str, List[str]]:
        spotlight_examples: Dict[str, List[str]] = {}
        if not collection.pull_request_examples:
            return spotlight_examples

        pr_lines = []
        for pr in collection.pull_request_examples[:3]:
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

    def _build_summary(
        self,
        period_label: str,
        total_activity: int,
        velocity_score: float,
        collaboration_score: float,
        stability_score: int,
    ) -> Dict[str, str]:
        return {
            "velocity": f"Average {velocity_score:.1f} commits per month",
            "collaboration": "{:.1f} combined PRs and reviews per month".format(collaboration_score),
            "stability": f"Net stability score of {stability_score}",
            "growth": f"{period_label} 동안 {total_activity}건의 활동을 기록했습니다.",
        }

    def _build_story_beats(
        self,
        collection: CollectionResult,
        period_label: str,
        total_activity: int,
    ) -> List[str]:
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

    def _determine_awards(self, collection: CollectionResult) -> List[str]:
        awards: List[str] = []
        if collection.commits >= 100:
            awards.append(
                "🏆 코드 대장장이 상 — 100회 이상의 커밋으로 저장소의 핵심을 단단하게 다졌습니다."
            )
        if collection.pull_requests >= 25:
            awards.append(
                "🚀 릴리스 선장 상 — 25건 이상의 Pull Request로 출시 흐름을 이끌었습니다."
            )
        if collection.reviews >= 20:
            awards.append(
                "🤝 성장 멘토 상 — 20회 이상 리뷰로 팀의 성장을 뒷받침했습니다."
            )
        if collection.issues and collection.issues <= max(collection.commits // 6, 1):
            awards.append(
                "🛡️ 안정 지킴이 상 — 활동 대비 적은 이슈로 안정성을 지켰습니다."
            )

        if not awards:
            awards.append(
                "🌟 만능 성장상 — 한 해의 작은 발걸음들이 내년의 큰 도약을 예고합니다."
            )

        return awards

    def _build_stats(self, collection: CollectionResult, velocity_score: float) -> Dict[str, Dict[str, float]]:
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

    def _build_evidence(self, collection: CollectionResult) -> Dict[str, List[str]]:
        repo_root = f"{self.web_base_url.rstrip('/')}/{collection.repo}"
        return {
            "commits": [
                f"{repo_root}/commits",
            ],
            "pull_requests": [
                f"{repo_root}/pulls",
            ],
        }
