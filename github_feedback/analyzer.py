"""Metric calculation logic for GitHub feedback analysis."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional

from .console import Console
from .models import (
    AnalysisStatus,
    CollectionResult,
    MetricSnapshot,
    DetailedFeedbackSnapshot,
    CommitMessageFeedback,
    PRTitleFeedback,
    ReviewToneFeedback,
    IssueFeedback,
)

console = Console()


@dataclass(slots=True)
class Analyzer:
    """Transform collected data into actionable metrics."""

    web_base_url: str = "https://github.com"

    def compute_metrics(
        self,
        collection: CollectionResult,
        detailed_feedback: Optional[DetailedFeedbackSnapshot] = None,
    ) -> MetricSnapshot:
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
            detailed_feedback=detailed_feedback,
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

        # Commit-based awards with tiers
        if collection.commits >= 1000:
            awards.append(
                "💎 코드 전설 상 (다이아몬드) — 1000회 이상의 커밋으로 저장소의 살아있는 역사를 썼습니다."
            )
        elif collection.commits >= 500:
            awards.append(
                "🏆 코드 마스터 상 (플래티넘) — 500회 이상의 커밋으로 코드베이스의 중추를 완성했습니다."
            )
        elif collection.commits >= 200:
            awards.append(
                "🥇 코드 대장장이 상 (골드) — 200회 이상의 커밋으로 저장소의 핵심을 단단하게 다졌습니다."
            )
        elif collection.commits >= 100:
            awards.append(
                "🥈 코드 장인 상 (실버) — 100회 이상의 커밋으로 꾸준한 개선을 이어갔습니다."
            )
        elif collection.commits >= 50:
            awards.append(
                "🥉 코드 견습생 상 (브론즈) — 50회 이상의 커밋으로 성장의 발판을 마련했습니다."
            )

        # Pull Request-based awards with tiers
        if collection.pull_requests >= 200:
            awards.append(
                "💎 릴리스 전설 상 (다이아몬드) — 200건 이상의 Pull Request로 배포의 새 역사를 열었습니다."
            )
        elif collection.pull_requests >= 100:
            awards.append(
                "🏆 배포 제독 상 (플래티넘) — 100건 이상의 Pull Request로 릴리스 함대를 지휘했습니다."
            )
        elif collection.pull_requests >= 50:
            awards.append(
                "🥇 릴리스 선장 상 (골드) — 50건 이상의 Pull Request로 출시 흐름을 이끌었습니다."
            )
        elif collection.pull_requests >= 25:
            awards.append(
                "🥈 릴리스 항해사 상 (실버) — 25건 이상의 Pull Request로 협업 릴리스를 주도했습니다."
            )
        elif collection.pull_requests >= 10:
            awards.append(
                "🥉 배포 선원 상 (브론즈) — 10건 이상의 Pull Request로 팀 배포에 기여했습니다."
            )

        # Review-based awards with tiers
        if collection.reviews >= 200:
            awards.append(
                "💎 지식 전파자 상 (다이아몬드) — 200회 이상의 리뷰로 팀 전체의 성장을 이끌었습니다."
            )
        elif collection.reviews >= 100:
            awards.append(
                "🏆 멘토링 대가 상 (플래티넘) — 100회 이상의 리뷰로 지식 공유 문화를 정착시켰습니다."
            )
        elif collection.reviews >= 50:
            awards.append(
                "🥇 리뷰 전문가 상 (골드) — 50회 이상의 리뷰로 코드 품질을 한 단계 끌어올렸습니다."
            )
        elif collection.reviews >= 20:
            awards.append(
                "🥈 성장 멘토 상 (실버) — 20회 이상의 리뷰로 팀의 성장을 뒷받침했습니다."
            )
        elif collection.reviews >= 10:
            awards.append(
                "🥉 코드 지원자 상 (브론즈) — 10회 이상의 리뷰로 동료를 도왔습니다."
            )

        # New category: Velocity-based awards
        month_span = max(collection.months, 1)
        velocity_score = collection.commits / month_span
        if velocity_score >= 50:
            awards.append(
                "⚡ 번개 개발자 상 — 월 평균 50회 이상의 커밋으로 놀라운 속도를 보여줬습니다."
            )
        elif velocity_score >= 20:
            awards.append(
                "🚀 속도왕 상 — 월 평균 20회 이상의 커밋으로 빠른 개발 템포를 유지했습니다."
            )

        # New category: Collaboration-based awards
        collaboration_score = (collection.pull_requests + collection.reviews) / month_span
        if collaboration_score >= 20:
            awards.append(
                "🤝 협업 마스터 상 — 월 평균 20회 이상의 PR과 리뷰로 팀워크의 중심이 되었습니다."
            )
        elif collaboration_score >= 10:
            awards.append(
                "👥 협업 전문가 상 — 월 평균 10회 이상의 PR과 리뷰로 팀 시너지를 강화했습니다."
            )

        # New category: All-rounder awards
        if (collection.commits >= 50 and
            collection.pull_requests >= 15 and
            collection.reviews >= 15):
            awards.append(
                "🌟 다재다능 상 — 커밋, PR, 리뷰 전 영역에서 균형잡힌 기여를 보여줬습니다."
            )

        # New category: Large-scale change awards
        if collection.pull_request_examples:
            max_change = max(
                (pr.additions + pr.deletions for pr in collection.pull_request_examples),
                default=0
            )
            if max_change >= 5000:
                awards.append(
                    "🏗️ 대규모 아키텍트 상 — 5000줄 이상의 변경으로 대담한 리팩터링을 완수했습니다."
                )
            elif max_change >= 2000:
                awards.append(
                    "🔨 대형 빌더 상 — 2000줄 이상의 변경으로 큰 규모의 개선을 이뤄냈습니다."
                )

        # New category: Consistency awards
        total_activity = collection.commits + collection.pull_requests + collection.reviews
        activity_per_month = total_activity / month_span
        if activity_per_month >= 30 and collection.months >= 6:
            awards.append(
                "📅 꾸준함의 달인 상 — 6개월 이상 월 평균 30회 이상의 활동으로 일관성을 입증했습니다."
            )
        elif activity_per_month >= 15 and collection.months >= 3:
            awards.append(
                "🔄 지속성 상 — 꾸준한 월별 활동으로 성실함을 보여줬습니다."
            )

        # Stability award (original)
        if collection.issues and collection.issues <= max(collection.commits // 6, 1):
            awards.append(
                "🛡️ 안정 지킴이 상 — 활동 대비 적은 이슈로 안정성을 지켰습니다."
            )

        # New category: Issue resolver awards
        if collection.issues >= 50:
            awards.append(
                "🔧 문제 해결사 상 — 50건 이상의 이슈를 다루며 저장소 품질을 개선했습니다."
            )
        elif collection.issues >= 20:
            awards.append(
                "🛠️ 버그 헌터 상 — 20건 이상의 이슈를 처리하며 안정성 확보에 기여했습니다."
            )

        # Default award if no other awards
        if not awards:
            awards.append(
                "🌱 성장 씨앗 상 — 작은 발걸음들이 모여 내일의 큰 성장을 준비하고 있습니다."
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

    def build_detailed_feedback(
        self,
        commit_analysis: Optional[Dict] = None,
        pr_title_analysis: Optional[Dict] = None,
        review_tone_analysis: Optional[Dict] = None,
        issue_analysis: Optional[Dict] = None,
    ) -> DetailedFeedbackSnapshot:
        """Build detailed feedback snapshot from LLM analysis results."""

        commit_feedback = None
        if commit_analysis:
            commit_feedback = CommitMessageFeedback(
                total_commits=commit_analysis.get("good_messages", 0)
                + commit_analysis.get("poor_messages", 0),
                good_messages=commit_analysis.get("good_messages", 0),
                poor_messages=commit_analysis.get("poor_messages", 0),
                suggestions=commit_analysis.get("suggestions", []),
                examples_good=commit_analysis.get("examples_good", []),
                examples_poor=commit_analysis.get("examples_poor", []),
            )

        pr_title_feedback = None
        if pr_title_analysis:
            pr_title_feedback = PRTitleFeedback(
                total_prs=pr_title_analysis.get("clear_titles", 0)
                + pr_title_analysis.get("vague_titles", 0),
                clear_titles=pr_title_analysis.get("clear_titles", 0),
                vague_titles=pr_title_analysis.get("vague_titles", 0),
                suggestions=pr_title_analysis.get("suggestions", []),
                examples_good=pr_title_analysis.get("examples_good", []),
                examples_poor=pr_title_analysis.get("examples_poor", []),
            )

        review_tone_feedback = None
        if review_tone_analysis:
            review_tone_feedback = ReviewToneFeedback(
                total_reviews=review_tone_analysis.get("constructive_reviews", 0)
                + review_tone_analysis.get("harsh_reviews", 0)
                + review_tone_analysis.get("neutral_reviews", 0),
                constructive_reviews=review_tone_analysis.get("constructive_reviews", 0),
                harsh_reviews=review_tone_analysis.get("harsh_reviews", 0),
                neutral_reviews=review_tone_analysis.get("neutral_reviews", 0),
                suggestions=review_tone_analysis.get("suggestions", []),
                examples_good=review_tone_analysis.get("examples_good", []),
                examples_improve=review_tone_analysis.get("examples_improve", []),
            )

        issue_feedback = None
        if issue_analysis:
            issue_feedback = IssueFeedback(
                total_issues=issue_analysis.get("well_described", 0)
                + issue_analysis.get("poorly_described", 0),
                well_described=issue_analysis.get("well_described", 0),
                poorly_described=issue_analysis.get("poorly_described", 0),
                suggestions=issue_analysis.get("suggestions", []),
                examples_good=issue_analysis.get("examples_good", []),
                examples_poor=issue_analysis.get("examples_poor", []),
            )

        return DetailedFeedbackSnapshot(
            commit_feedback=commit_feedback,
            pr_title_feedback=pr_title_feedback,
            review_tone_feedback=review_tone_feedback,
            issue_feedback=issue_feedback,
        )
