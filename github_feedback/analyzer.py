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
    MonthlyTrend,
    TechStackAnalysis,
    CollaborationNetwork,
    ReflectionPrompts,
    YearEndReview,
)

console = Console()


# Award tier configurations
AWARD_TIERS = {
    "commits": [
        (1000, "💎 코드 전설 상 (다이아몬드) — 1000회 이상의 커밋으로 저장소의 살아있는 역사를 썼습니다."),
        (500, "🏆 코드 마스터 상 (플래티넘) — 500회 이상의 커밋으로 코드베이스의 중추를 완성했습니다."),
        (200, "🥇 코드 대장장이 상 (골드) — 200회 이상의 커밋으로 저장소의 핵심을 단단하게 다졌습니다."),
        (100, "🥈 코드 장인 상 (실버) — 100회 이상의 커밋으로 꾸준한 개선을 이어갔습니다."),
        (50, "🥉 코드 견습생 상 (브론즈) — 50회 이상의 커밋으로 성장의 발판을 마련했습니다."),
    ],
    "pull_requests": [
        (200, "💎 릴리스 전설 상 (다이아몬드) — 200건 이상의 Pull Request로 배포의 새 역사를 열었습니다."),
        (100, "🏆 배포 제독 상 (플래티넘) — 100건 이상의 Pull Request로 릴리스 함대를 지휘했습니다."),
        (50, "🥇 릴리스 선장 상 (골드) — 50건 이상의 Pull Request로 출시 흐름을 이끌었습니다."),
        (25, "🥈 릴리스 항해사 상 (실버) — 25건 이상의 Pull Request로 협업 릴리스를 주도했습니다."),
        (10, "🥉 배포 선원 상 (브론즈) — 10건 이상의 Pull Request로 팀 배포에 기여했습니다."),
    ],
    "reviews": [
        (200, "💎 지식 전파자 상 (다이아몬드) — 200회 이상의 리뷰로 팀 전체의 성장을 이끌었습니다."),
        (100, "🏆 멘토링 대가 상 (플래티넘) — 100회 이상의 리뷰로 지식 공유 문화를 정착시켰습니다."),
        (50, "🥇 리뷰 전문가 상 (골드) — 50회 이상의 리뷰로 코드 품질을 한 단계 끌어올렸습니다."),
        (20, "🥈 성장 멘토 상 (실버) — 20회 이상의 리뷰로 팀의 성장을 뒷받침했습니다."),
        (10, "🥉 코드 지원자 상 (브론즈) — 10회 이상의 리뷰로 동료를 도왔습니다."),
    ],
    "issues": [
        (50, "🔧 문제 해결사 상 — 50건 이상의 이슈를 다루며 저장소 품질을 개선했습니다."),
        (20, "🛠️ 버그 헌터 상 — 20건 이상의 이슈를 처리하며 안정성 확보에 기여했습니다."),
    ],
    "velocity": [
        (50, "⚡ 번개 개발자 상 — 월 평균 50회 이상의 커밋으로 놀라운 속도를 보여줬습니다."),
        (20, "🚀 속도왕 상 — 월 평균 20회 이상의 커밋으로 빠른 개발 템포를 유지했습니다."),
    ],
    "collaboration": [
        (20, "🤝 협업 마스터 상 — 월 평균 20회 이상의 PR과 리뷰로 팀워크의 중심이 되었습니다."),
        (10, "👥 협업 전문가 상 — 월 평균 10회 이상의 PR과 리뷰로 팀 시너지를 강화했습니다."),
    ],
    "activity_consistency": [
        ((30, 6), "📅 꾸준함의 달인 상 — 6개월 이상 월 평균 30회 이상의 활동으로 일관성을 입증했습니다."),
        ((15, 3), "🔄 지속성 상 — 꾸준한 월별 활동으로 성실함을 보여줬습니다."),
    ],
    "change_scale": [
        (5000, "🏗️ 대규모 아키텍트 상 — 5000줄 이상의 변경으로 대담한 리팩터링을 완수했습니다."),
        (2000, "🔨 대형 빌더 상 — 2000줄 이상의 변경으로 큰 규모의 개선을 이뤄냈습니다."),
    ],
}


@dataclass(slots=True)
class Analyzer:
    """Transform collected data into actionable metrics."""

    web_base_url: str = "https://github.com"

    def compute_metrics(
        self,
        collection: CollectionResult,
        detailed_feedback: Optional[DetailedFeedbackSnapshot] = None,
        monthly_trends_data: Optional[List[Dict]] = None,
        tech_stack_data: Optional[Dict[str, int]] = None,
        collaboration_data: Optional[Dict[str, Any]] = None,
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

        # Build year-end specific insights
        monthly_trends = self._build_monthly_trends(monthly_trends_data)
        tech_stack = self._build_tech_stack_analysis(tech_stack_data)
        collaboration = self._build_collaboration_network(collaboration_data)
        reflection_prompts = self._build_reflection_prompts(collection)
        year_end_review = self._build_year_end_review(collection, highlights, awards)

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
            monthly_trends=monthly_trends,
            tech_stack=tech_stack,
            collaboration=collaboration,
            reflection_prompts=reflection_prompts,
            year_end_review=year_end_review,
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

        # Sort PRs by change volume (largest first) to show most significant contributions
        sorted_prs = sorted(
            collection.pull_request_examples,
            key=lambda pr: pr.additions + pr.deletions,
            reverse=True
        )

        pr_lines = []
        for idx, pr in enumerate(sorted_prs[:5], 1):
            change_volume = pr.additions + pr.deletions
            scale_phrase = f"변경 {change_volume:,}줄" if change_volume else "경량 변경"
            merged_phrase = (
                f"{pr.merged_at.date().isoformat()} 병합"
                if pr.merged_at
                else "미병합"
            )

            # Add reason for showing this PR
            if idx == 1:
                reason = "최대 변경량"
            elif idx == 2:
                reason = "2번째 큰 변경"
            elif idx == 3:
                reason = "3번째 큰 변경"
            elif change_volume > 500:
                reason = "대규모 변경"
            else:
                reason = "주요 기여"

            pr_lines.append(
                f"PR #{pr.number} · {pr.title} — {pr.author} ({pr.created_at.date().isoformat()}, {merged_phrase}, {scale_phrase}) · [{reason}] · {pr.html_url}"
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
        """Determine awards based on collection metrics using data-driven tier system."""
        awards: List[str] = []
        month_span = max(collection.months, 1)

        # Apply tier-based awards
        self._add_tier_award(awards, "commits", collection.commits)
        self._add_tier_award(awards, "pull_requests", collection.pull_requests)
        self._add_tier_award(awards, "reviews", collection.reviews)
        self._add_tier_award(awards, "issues", collection.issues)

        # Velocity-based awards
        velocity_score = collection.commits / month_span
        self._add_tier_award(awards, "velocity", velocity_score)

        # Collaboration-based awards
        collaboration_score = (collection.pull_requests + collection.reviews) / month_span
        self._add_tier_award(awards, "collaboration", collaboration_score)

        # Activity consistency awards
        total_activity = collection.commits + collection.pull_requests + collection.reviews
        activity_per_month = total_activity / month_span
        for (threshold_activity, threshold_months), award_text in AWARD_TIERS["activity_consistency"]:
            if activity_per_month >= threshold_activity and collection.months >= threshold_months:
                awards.append(award_text)
                break

        # All-rounder award
        if (collection.commits >= 50 and
            collection.pull_requests >= 15 and
            collection.reviews >= 15):
            awards.append(
                "🌟 다재다능 상 — 커밋, PR, 리뷰 전 영역에서 균형잡힌 기여를 보여줬습니다."
            )

        # Large-scale change awards
        if collection.pull_request_examples:
            max_change = max(
                (pr.additions + pr.deletions for pr in collection.pull_request_examples),
                default=0
            )
            self._add_tier_award(awards, "change_scale", max_change)

        # Stability award
        if collection.issues and collection.issues <= max(collection.commits // 6, 1):
            awards.append(
                "🛡️ 안정 지킴이 상 — 활동 대비 적은 이슈로 안정성을 지켰습니다."
            )

        # Default award if no other awards
        if not awards:
            awards.append(
                "🌱 성장 씨앗 상 — 작은 발걸음들이 모여 내일의 큰 성장을 준비하고 있습니다."
            )

        return awards

    @staticmethod
    def _add_tier_award(awards: List[str], category: str, value: float) -> None:
        """Add tier-based award if value meets threshold.

        Args:
            awards: List to append awards to
            category: Award category key from AWARD_TIERS
            value: Metric value to check against thresholds
        """
        if category not in AWARD_TIERS:
            return

        for threshold, award_text in AWARD_TIERS[category]:
            if value >= threshold:
                awards.append(award_text)
                break

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

    def _build_monthly_trends(
        self, monthly_trends_data: Optional[List[Dict]]
    ) -> List[MonthlyTrend]:
        """Build monthly trend objects from raw data."""
        if not monthly_trends_data:
            return []

        trends = []
        for data in monthly_trends_data:
            trends.append(
                MonthlyTrend(
                    month=data.get("month", ""),
                    commits=data.get("commits", 0),
                    pull_requests=data.get("pull_requests", 0),
                    reviews=data.get("reviews", 0),
                    issues=data.get("issues", 0),
                )
            )
        return trends

    def _build_tech_stack_analysis(
        self, tech_stack_data: Optional[Dict[str, int]]
    ) -> Optional[TechStackAnalysis]:
        """Analyze technology stack from file changes."""
        if not tech_stack_data:
            return None

        # Calculate top languages
        sorted_languages = sorted(
            tech_stack_data.items(), key=lambda x: x[1], reverse=True
        )
        top_languages = [lang for lang, _ in sorted_languages[:5]]

        # Calculate diversity score (Shannon entropy normalized)
        total_files = sum(tech_stack_data.values())
        if total_files == 0:
            diversity_score = 0.0
        else:
            import math
            entropy = 0.0
            for count in tech_stack_data.values():
                if count > 0:
                    p = count / total_files
                    entropy -= p * math.log2(p)
            # Normalize to 0-1 range (max entropy is log2(n))
            max_entropy = math.log2(len(tech_stack_data)) if len(tech_stack_data) > 1 else 1
            diversity_score = entropy / max_entropy if max_entropy > 0 else 0.0

        return TechStackAnalysis(
            languages=tech_stack_data,
            top_languages=top_languages,
            diversity_score=diversity_score,
        )

    def _build_collaboration_network(
        self, collaboration_data: Optional[Dict[str, Any]]
    ) -> Optional[CollaborationNetwork]:
        """Build collaboration network from reviewer data."""
        if not collaboration_data:
            return None

        pr_reviewers = collaboration_data.get("pr_reviewers", {})
        sorted_reviewers = sorted(
            pr_reviewers.items(), key=lambda x: x[1], reverse=True
        )
        top_reviewers = [reviewer for reviewer, _ in sorted_reviewers[:5]]

        return CollaborationNetwork(
            pr_reviewers=pr_reviewers,
            top_reviewers=top_reviewers,
            review_received_count=collaboration_data.get("review_received_count", 0),
            unique_collaborators=collaboration_data.get("unique_collaborators", 0),
        )

    def _build_reflection_prompts(
        self, collection: CollectionResult
    ) -> ReflectionPrompts:
        """Generate self-reflection questions for year-end review."""
        questions = [
            "올해 내가 가장 자랑스러워하는 기술적 성취는 무엇인가요?",
            "가장 어려웠던 기술적 도전은 무엇이었고, 어떻게 극복했나요?",
            "올해 새롭게 배운 기술이나 도구 중 가장 유용했던 것은 무엇인가요?",
            "코드 리뷰를 통해 받은 피드백 중 가장 기억에 남는 것은 무엇인가요?",
            "팀원들과의 협업에서 가장 뿌듯했던 순간은 언제였나요?",
            "내 코드가 팀이나 사용자에게 가장 큰 영향을 준 순간은 언제였나요?",
            "올해 내 개발 프로세스나 습관에서 개선된 점은 무엇인가요?",
            "앞으로 더 발전시키고 싶은 기술 영역은 무엇인가요?",
            "내년에 도전하고 싶은 새로운 프로젝트나 기술은 무엇인가요?",
            "개발자로서 내년의 나는 어떤 모습이길 바라나요?",
        ]

        # Add context-specific questions based on activity
        if collection.commits > 100:
            questions.append(
                f"올해 {collection.commits}회의 커밋을 작성했습니다. 이 중 가장 의미있었던 커밋은 무엇이었나요?"
            )

        if collection.reviews > 50:
            questions.append(
                f"{collection.reviews}회의 코드 리뷰를 진행했습니다. 리뷰를 통해 배운 것은 무엇인가요?"
            )

        if collection.pull_requests > 30:
            questions.append(
                f"{collection.pull_requests}개의 Pull Request를 작성했습니다. 가장 복잡했던 PR은 무엇이었고, 어떤 점이 어려웠나요?"
            )

        return ReflectionPrompts(questions=questions)

    def _build_year_end_review(
        self,
        collection: CollectionResult,
        highlights: List[str],
        awards: List[str],
    ) -> YearEndReview:
        """Generate year-end specific review content."""

        # Proudest moments based on metrics
        proudest_moments = []
        if collection.commits > 200:
            proudest_moments.append(
                f"총 {collection.commits}회의 커밋으로 꾸준히 코드베이스를 개선했습니다."
            )
        if collection.pull_requests > 50:
            proudest_moments.append(
                f"{collection.pull_requests}개의 Pull Request를 성공적으로 머지했습니다."
            )
        if collection.reviews > 50:
            proudest_moments.append(
                f"{collection.reviews}회의 코드 리뷰로 팀의 코드 품질 향상에 기여했습니다."
            )
        if not proudest_moments:
            proudest_moments.append(
                "꾸준한 활동으로 프로젝트 발전에 기여했습니다."
            )

        # Challenges (generic, to be filled by user)
        biggest_challenges = [
            "복잡한 기술적 문제를 해결하며 문제 해결 능력을 키웠습니다.",
            "새로운 기술 스택을 학습하고 프로젝트에 적용했습니다.",
            "팀원들과의 협업을 통해 커뮤니케이션 스킬을 향상시켰습니다.",
        ]

        # Lessons learned
        lessons_learned = [
            "작고 자주 커밋하는 것이 코드 리뷰와 협업에 더 효과적입니다.",
            "코드 리뷰는 단순한 버그 찾기가 아닌 지식 공유의 장입니다.",
            "좋은 커밋 메시지와 PR 설명은 미래의 나와 팀원들을 위한 투자입니다.",
        ]

        # Next year goals
        next_year_goals = [
            "새로운 프로그래밍 언어나 프레임워크를 학습하여 기술 스택 다변화",
            "오픈소스 프로젝트에 기여하여 커뮤니티 참여 확대",
            "기술 블로그나 발표를 통해 배운 내용을 공유",
            "코드 품질과 테스트 커버리지 개선에 더 집중",
            "멘토링을 통해 주니어 개발자 성장 지원",
        ]

        return YearEndReview(
            proudest_moments=proudest_moments,
            biggest_challenges=biggest_challenges,
            lessons_learned=lessons_learned,
            next_year_goals=next_year_goals,
        )
