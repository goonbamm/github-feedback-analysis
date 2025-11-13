"""Metric calculation logic for GitHub feedback analysis."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List, NamedTuple, Optional

from .award_strategies import AwardCalculator
from .console import Console
from .constants import (
    ACTIVITY_THRESHOLDS,
    COLLECTION_LIMITS,
    CONSISTENCY_THRESHOLDS,
    DISPLAY_LIMITS,
    TREND_THRESHOLDS,
)
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
    MonthlyTrendInsights,
    TechStackAnalysis,
    CollaborationNetwork,
    ReflectionPrompts,
    YearEndReview,
)
from .retrospective import RetrospectiveAnalyzer

console = Console()


class PeriodFormatter:
    """Format period labels based on month count."""

    # Mapping of common month counts to Korean labels
    LABEL_MAP = {
        3: "최근 3개월",
        6: "최근 6개월",
        12: "최근 1년",
    }

    @staticmethod
    def format_period(months: int) -> str:
        """Format period label based on month count.

        Args:
            months: Number of months in the period

        Returns:
            Formatted period label in Korean

        Examples:
            >>> PeriodFormatter.format_period(3)
            '최근 3개월'
            >>> PeriodFormatter.format_period(12)
            '최근 1년'
            >>> PeriodFormatter.format_period(25)
            '최근 2년 1개월'
        """
        # Check for exact matches first
        if months in PeriodFormatter.LABEL_MAP:
            return PeriodFormatter.LABEL_MAP[months]

        # Handle years and remaining months
        if months >= 24:
            years = months // 12
            remaining_months = months % 12
            if remaining_months == 0:
                return f"최근 {years}년"
            return f"최근 {years}년 {remaining_months}개월"

        # Default to months
        return f"최근 {months}개월"


class CollectionStats(NamedTuple):
    """Statistics computed from collection data."""
    month_span: int
    velocity_score: float
    collaboration_score: float
    stability_score: int
    total_activity: int
    period_label: str


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

        stats = self._calculate_scores(collection)

        highlights = self._build_highlights(
            collection,
            stats.period_label,
            stats.month_span,
            stats.velocity_score,
            stats.total_activity,
        )
        spotlight_examples = self._build_spotlight_examples(collection)
        summary = self._build_summary(
            stats.period_label,
            stats.total_activity,
            stats.velocity_score,
            stats.collaboration_score,
            stats.stability_score,
        )
        story_beats = self._build_story_beats(collection, stats.period_label, stats.total_activity)
        awards = self._determine_awards(collection)
        metric_stats = self._build_stats(collection, stats.velocity_score)
        evidence = self._build_evidence(collection)

        # Build year-end specific insights
        monthly_trends = self._build_monthly_trends(monthly_trends_data)
        monthly_insights = self._build_monthly_insights(monthly_trends)
        tech_stack = self._build_tech_stack_analysis(tech_stack_data)
        collaboration = self._build_collaboration_network(collaboration_data)
        reflection_prompts = self._build_reflection_prompts(collection)
        year_end_review = self._build_year_end_review(collection, highlights, awards)

        # Create initial metrics snapshot
        metrics_snapshot = MetricSnapshot(
            repo=collection.repo,
            months=collection.months,
            generated_at=datetime.now(timezone.utc),
            status=AnalysisStatus.ANALYSED,
            summary=summary,
            stats=metric_stats,
            evidence=evidence,
            highlights=highlights,
            spotlight_examples=spotlight_examples,
            yearbook_story=story_beats,
            awards=awards,
            detailed_feedback=detailed_feedback,
            monthly_trends=monthly_trends,
            monthly_insights=monthly_insights,
            tech_stack=tech_stack,
            collaboration=collaboration,
            reflection_prompts=reflection_prompts,
            year_end_review=year_end_review,
            since_date=collection.since_date,
            until_date=collection.until_date,
        )

        # Generate comprehensive retrospective analysis
        console.log("Generating retrospective analysis", f"repo={collection.repo}")
        retrospective_analyzer = RetrospectiveAnalyzer()
        retrospective = retrospective_analyzer.analyze(metrics_snapshot)
        metrics_snapshot.retrospective = retrospective

        return metrics_snapshot

    def _calculate_scores(
        self, collection: CollectionResult
    ) -> CollectionStats:
        month_span = max(collection.months, 1)
        velocity_score = collection.commits / month_span
        collaboration_score = (collection.pull_requests + collection.reviews) / month_span
        stability_score = max(collection.commits - collection.issues, 0)
        total_activity = collection.commits + collection.pull_requests + collection.reviews
        period_label = PeriodFormatter.format_period(collection.months)

        return CollectionStats(
            month_span=month_span,
            velocity_score=velocity_score,
            collaboration_score=collaboration_score,
            stability_score=stability_score,
            total_activity=total_activity,
            period_label=period_label,
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
        """Determine awards based on collection metrics using Strategy pattern.

        This method delegates award calculation to the AwardCalculator,
        which orchestrates multiple award strategies.

        Args:
            collection: Collection of repository data

        Returns:
            List of award strings
        """
        calculator = AwardCalculator()
        return calculator.determine_awards(collection)

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

    def _build_commit_feedback(self, analysis: Dict) -> CommitMessageFeedback:
        """Build commit message feedback from analysis."""
        return CommitMessageFeedback(
            total_commits=analysis.get("good_messages", 0) + analysis.get("poor_messages", 0),
            good_messages=analysis.get("good_messages", 0),
            poor_messages=analysis.get("poor_messages", 0),
            suggestions=analysis.get("suggestions", []),
            examples_good=analysis.get("examples_good", []),
            examples_poor=analysis.get("examples_poor", []),
        )

    def _build_pr_title_feedback(self, analysis: Dict) -> PRTitleFeedback:
        """Build PR title feedback from analysis."""
        return PRTitleFeedback(
            total_prs=analysis.get("clear_titles", 0) + analysis.get("vague_titles", 0),
            clear_titles=analysis.get("clear_titles", 0),
            vague_titles=analysis.get("vague_titles", 0),
            suggestions=analysis.get("suggestions", []),
            examples_good=analysis.get("examples_good", []),
            examples_poor=analysis.get("examples_poor", []),
        )

    def _build_review_tone_feedback(self, analysis: Dict) -> ReviewToneFeedback:
        """Build review tone feedback from analysis."""
        return ReviewToneFeedback(
            total_reviews=analysis.get("constructive_reviews", 0)
            + analysis.get("harsh_reviews", 0)
            + analysis.get("neutral_reviews", 0),
            constructive_reviews=analysis.get("constructive_reviews", 0),
            harsh_reviews=analysis.get("harsh_reviews", 0),
            neutral_reviews=analysis.get("neutral_reviews", 0),
            suggestions=analysis.get("suggestions", []),
            examples_good=analysis.get("examples_good", []),
            examples_improve=analysis.get("examples_improve", []),
        )

    def _build_issue_feedback(self, analysis: Dict) -> IssueFeedback:
        """Build issue feedback from analysis."""
        return IssueFeedback(
            total_issues=analysis.get("well_described", 0) + analysis.get("poorly_described", 0),
            well_described=analysis.get("well_described", 0),
            poorly_described=analysis.get("poorly_described", 0),
            suggestions=analysis.get("suggestions", []),
            examples_good=analysis.get("examples_good", []),
            examples_poor=analysis.get("examples_poor", []),
        )

    def build_detailed_feedback(
        self,
        commit_analysis: Optional[Dict] = None,
        pr_title_analysis: Optional[Dict] = None,
        review_tone_analysis: Optional[Dict] = None,
        issue_analysis: Optional[Dict] = None,
    ) -> DetailedFeedbackSnapshot:
        """Build detailed feedback snapshot from LLM analysis results."""

        return DetailedFeedbackSnapshot(
            commit_feedback=self._build_commit_feedback(commit_analysis) if commit_analysis else None,
            pr_title_feedback=self._build_pr_title_feedback(pr_title_analysis) if pr_title_analysis else None,
            review_tone_feedback=self._build_review_tone_feedback(review_tone_analysis) if review_tone_analysis else None,
            issue_feedback=self._build_issue_feedback(issue_analysis) if issue_analysis else None,
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

    def _calculate_trend_direction(self, monthly_activities: List[tuple]) -> str:
        """Calculate trend direction from monthly activities."""
        if len(monthly_activities) < TREND_THRESHOLDS['minimum_months_for_trend']:
            return "stable"

        recent_half = monthly_activities[len(monthly_activities)//2:]
        early_half = monthly_activities[:len(monthly_activities)//2]

        recent_avg = sum(act for _, act in recent_half) / len(recent_half) if recent_half else 0
        early_avg = sum(act for _, act in early_half) / len(early_half) if early_half else 0

        if recent_avg > early_avg * TREND_THRESHOLDS['increasing_multiplier']:
            return "increasing"
        elif recent_avg < early_avg * TREND_THRESHOLDS['decreasing_multiplier']:
            return "decreasing"
        else:
            return "stable"

    def _calculate_consistency_score(self, monthly_activities: List[tuple]) -> float:
        """Calculate consistency score from monthly activities."""
        activities = [act for _, act in monthly_activities if act > 0]
        if not activities or len(activities) < 2:
            return 0.0

        import math
        mean_activity = sum(activities) / len(activities)
        variance = sum((act - mean_activity) ** 2 for act in activities) / len(activities)
        std_dev = math.sqrt(variance)

        # Coefficient of variation (lower is more consistent)
        cv = std_dev / mean_activity if mean_activity > 0 else 1.0
        # Convert to 0-1 score (1 = perfect consistency, 0 = highly variable)
        return max(0.0, 1.0 - min(cv, 1.0))

    def _generate_trend_insights(
        self,
        monthly_trends: List[MonthlyTrend],
        monthly_activities: List[tuple],
        peak_month: Optional[str],
        quiet_month: Optional[str],
        trend_direction: str,
        consistency_score: float,
    ) -> List[str]:
        """Generate human-readable insights from trend data."""
        insights = []

        if peak_month:
            peak_activity = next((act for month, act in monthly_activities if month == peak_month), 0)
            insights.append(
                f"{peak_month}에 가장 활발했습니다 (총 {peak_activity}건의 활동)"
            )

        if quiet_month and quiet_month != peak_month:
            quiet_activity = next((act for month, act in monthly_activities if month == quiet_month), 0)
            insights.append(
                f"{quiet_month}에는 상대적으로 조용했습니다 (총 {quiet_activity}건의 활동)"
            )

        if trend_direction == "increasing":
            insights.append(
                "시간이 지날수록 활동량이 증가하는 성장 추세를 보였습니다"
            )
        elif trend_direction == "decreasing":
            insights.append(
                "최근 활동량이 감소하는 경향이 있습니다. 새로운 동기 부여가 필요할 수 있습니다"
            )
        else:
            insights.append(
                "꾸준한 활동 수준을 유지했습니다"
            )

        if consistency_score > CONSISTENCY_THRESHOLDS['very_consistent']:
            insights.append(
                f"매우 일관된 활동 패턴을 보였습니다 (일관성 점수: {consistency_score:.1%})"
            )
        elif consistency_score < CONSISTENCY_THRESHOLDS['inconsistent']:
            insights.append(
                f"활동량의 변동이 큰 편입니다 (일관성 점수: {consistency_score:.1%}). "
                "더 균형잡힌 기여 리듬을 만들어보세요"
            )

        # Analyze specific activity types
        commits_trend = [trend.commits for trend in monthly_trends]
        prs_trend = [trend.pull_requests for trend in monthly_trends]

        if commits_trend and max(commits_trend) > 0:
            peak_commit_month = monthly_trends[commits_trend.index(max(commits_trend))].month
            insights.append(
                f"커밋 활동은 {peak_commit_month}에 정점을 찍었습니다 ({max(commits_trend)}회)"
            )

        if prs_trend and max(prs_trend) > 0:
            peak_pr_month = monthly_trends[prs_trend.index(max(prs_trend))].month
            if max(prs_trend) >= ACTIVITY_THRESHOLDS['moderate_prs']:
                insights.append(
                    f"PR 활동은 {peak_pr_month}에 가장 왕성했습니다 ({max(prs_trend)}개)"
                )

        return insights

    def _build_monthly_insights(
        self, monthly_trends: List[MonthlyTrend]
    ) -> Optional[MonthlyTrendInsights]:
        """Analyze monthly trends and generate insights."""
        if not monthly_trends or len(monthly_trends) < 2:
            return None

        # Calculate total activity per month
        monthly_activities = [
            (trend.month, trend.commits + trend.pull_requests + trend.reviews + trend.issues)
            for trend in monthly_trends
        ]

        # Find peak and quiet months
        peak_month_data = max(monthly_activities, key=lambda x: x[1])
        peak_month = peak_month_data[0] if peak_month_data[1] > 0 else None

        non_zero_activities = [(month, activity) for month, activity in monthly_activities if activity > 0]
        quiet_month = None
        if non_zero_activities:
            quiet_month_data = min(non_zero_activities, key=lambda x: x[1])
            quiet_month = quiet_month_data[0]

        # Calculate active months
        total_active_months = sum(1 for _, activity in monthly_activities if activity > 0)

        # Calculate metrics
        trend_direction = self._calculate_trend_direction(monthly_activities)
        consistency_score = self._calculate_consistency_score(monthly_activities)

        # Generate insights
        insights = self._generate_trend_insights(
            monthly_trends,
            monthly_activities,
            peak_month,
            quiet_month,
            trend_direction,
            consistency_score,
        )

        return MonthlyTrendInsights(
            peak_month=peak_month,
            quiet_month=quiet_month,
            trend_direction=trend_direction,
            total_active_months=total_active_months,
            consistency_score=consistency_score,
            insights=insights,
        )

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
        top_languages = [lang for lang, _ in sorted_languages[:DISPLAY_LIMITS['top_languages']]]

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
        top_reviewers = [reviewer for reviewer, _ in sorted_reviewers[:DISPLAY_LIMITS['top_reviewers']]]

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
        if collection.commits > ACTIVITY_THRESHOLDS['high_commits']:
            questions.append(
                f"올해 {collection.commits}회의 커밋을 작성했습니다. 이 중 가장 의미있었던 커밋은 무엇이었나요?"
            )

        if collection.reviews > ACTIVITY_THRESHOLDS['very_high_reviews']:
            questions.append(
                f"{collection.reviews}회의 코드 리뷰를 진행했습니다. 리뷰를 통해 배운 것은 무엇인가요?"
            )

        if collection.pull_requests > ACTIVITY_THRESHOLDS['high_prs']:
            questions.append(
                f"{collection.pull_requests}개의 Pull Request를 작성했습니다. 가장 복잡했던 PR은 무엇이었고, 어떤 점이 어려웠나요?"
            )

        return ReflectionPrompts(questions=questions)

    def _extract_proudest_moments(self, collection: CollectionResult) -> List[str]:
        """Extract proudest moments from collection data."""
        moments = []

        if collection.commits > ACTIVITY_THRESHOLDS['very_high_commits']:
            moments.append(
                f"총 {collection.commits}회의 커밋으로 꾸준히 코드베이스를 개선했습니다."
            )
        if collection.pull_requests > ACTIVITY_THRESHOLDS['very_high_prs']:
            moments.append(
                f"{collection.pull_requests}개의 Pull Request를 성공적으로 머지했습니다."
            )
        if collection.reviews > ACTIVITY_THRESHOLDS['very_high_reviews']:
            moments.append(
                f"{collection.reviews}회의 코드 리뷰로 팀의 코드 품질 향상에 기여했습니다."
            )

        # Add insights from PR examples
        if collection.pull_request_examples:
            total_changes = sum(pr.additions + pr.deletions for pr in collection.pull_request_examples)
            if total_changes > ACTIVITY_THRESHOLDS['very_large_pr']:
                moments.append(
                    f"총 {total_changes:,}줄의 코드 변경으로 대규모 개선을 주도했습니다."
                )

            # Find largest PR
            largest_pr = max(collection.pull_request_examples,
                           key=lambda pr: pr.additions + pr.deletions)
            if (largest_pr.additions + largest_pr.deletions) > ACTIVITY_THRESHOLDS['large_pr']:
                moments.append(
                    f"가장 큰 PR(#{largest_pr.number}: {largest_pr.title})에서 "
                    f"{largest_pr.additions + largest_pr.deletions:,}줄의 변경으로 도전적인 작업을 완수했습니다."
                )

        if not moments:
            moments.append("꾸준한 활동으로 프로젝트 발전에 기여했습니다.")

        return moments

    def _extract_biggest_challenges(self, collection: CollectionResult) -> List[str]:
        """Extract biggest challenges from collection data."""
        challenges = []
        month_span = max(collection.months, 1)

        if collection.pull_requests > ACTIVITY_THRESHOLDS['high_prs']:
            avg_pr_per_month = collection.pull_requests / month_span
            challenges.append(
                f"월평균 {avg_pr_per_month:.1f}개의 PR을 관리하며 지속적인 배포 리듬을 유지하는 도전을 해냈습니다."
            )

        if collection.reviews > ACTIVITY_THRESHOLDS['high_reviews']:
            challenges.append(
                f"{collection.reviews}회의 코드 리뷰를 진행하며 팀원들의 다양한 관점을 이해하고 조율했습니다."
            )

        if collection.issues > 0:
            challenges.append(
                f"{collection.issues}건의 이슈를 처리하며 문제 해결 능력과 우선순위 판단 능력을 키웠습니다."
            )

        # Add PR-specific challenges
        if collection.pull_request_examples:
            feature_prs = [pr for pr in collection.pull_request_examples
                         if any(kw in pr.title.lower() for kw in ['feature', 'feat', '기능', 'add'])]
            if len(feature_prs) > ACTIVITY_THRESHOLDS['feature_pr_threshold']:
                challenges.append(
                    f"{len(feature_prs)}개의 새로운 기능을 개발하며 요구사항 분석과 설계 능력을 향상시켰습니다."
                )

        if not challenges:
            challenges = [
                "복잡한 기술적 문제를 해결하며 문제 해결 능력을 키웠습니다.",
                "팀원들과의 협업을 통해 커뮤니케이션 스킬을 향상시켰습니다.",
            ]

        return challenges

    def _extract_lessons_learned(self, collection: CollectionResult) -> List[str]:
        """Extract lessons learned from collection data."""
        lessons = []

        if collection.commits > 0 and collection.pull_requests > 0:
            commits_per_pr = collection.commits / collection.pull_requests
            if commits_per_pr > ACTIVITY_THRESHOLDS['high_commits_per_pr']:
                lessons.append(
                    f"PR당 평균 {commits_per_pr:.1f}개의 커밋을 작성했습니다. "
                    "작은 단위로 자주 커밋하고 리뷰받는 것이 더 효과적일 수 있습니다."
                )
            else:
                lessons.append(
                    f"PR당 평균 {commits_per_pr:.1f}개의 커밋으로 적절한 크기의 변경을 유지했습니다. "
                    "작고 집중된 PR이 리뷰와 병합을 더 쉽게 만듭니다."
                )

        if collection.reviews > 0 and collection.pull_requests > 0:
            review_ratio = collection.reviews / collection.pull_requests
            if review_ratio > ACTIVITY_THRESHOLDS['high_review_ratio']:
                lessons.append(
                    f"내 PR보다 {review_ratio:.1f}배 많은 리뷰를 진행했습니다. "
                    "코드 리뷰는 팀의 코드 품질을 높이고 지식을 공유하는 핵심 활동입니다."
                )
            else:
                lessons.append(
                    "코드 리뷰를 통해 다른 팀원들의 접근 방식을 배우고 시야를 넓힐 수 있었습니다."
                )

        if collection.pull_request_examples:
            merged_prs = [pr for pr in collection.pull_request_examples if pr.merged_at]
            if merged_prs:
                merge_rate = len(merged_prs) / len(collection.pull_request_examples)
                if merge_rate > ACTIVITY_THRESHOLDS['high_merge_rate']:
                    lessons.append(
                        f"{merge_rate*100:.0f}%의 높은 PR 머지율을 달성했습니다. "
                        "명확한 목적과 충분한 설명이 있는 PR이 성공률을 높입니다."
                    )

        if not lessons:
            lessons = [
                "작고 자주 커밋하는 것이 코드 리뷰와 협업에 더 효과적입니다.",
                "코드 리뷰는 단순한 버그 찾기가 아닌 지식 공유의 장입니다.",
            ]

        return lessons

    def _extract_next_year_goals(self, collection: CollectionResult) -> List[str]:
        """Extract next year goals from collection data."""
        goals = []

        # Goals based on current weak points
        if collection.reviews < collection.pull_requests:
            goals.append(
                "코드 리뷰 참여를 늘려 팀의 코드 품질 향상에 더욱 기여하기"
            )

        if collection.pull_request_examples:
            doc_prs = [pr for pr in collection.pull_request_examples
                      if any(kw in pr.title.lower() for kw in ['doc', 'readme', '문서'])]
            if len(doc_prs) < ACTIVITY_THRESHOLDS['moderate_doc_prs']:
                goals.append(
                    "문서화에 더 신경써서 프로젝트의 접근성과 유지보수성 향상하기"
                )

            test_prs = [pr for pr in collection.pull_request_examples
                       if any(kw in pr.title.lower() for kw in ['test', '테스트'])]
            if len(test_prs) < ACTIVITY_THRESHOLDS['moderate_test_prs']:
                goals.append(
                    "테스트 커버리지를 높여 코드의 안정성과 신뢰도 강화하기"
                )

        # Always include growth goals
        goals.append(
            "새로운 기술이나 프레임워크를 학습하여 기술 스택 확장하기"
        )
        goals.append(
            "오픈소스 기여나 기술 공유를 통해 개발 커뮤니티에 환원하기"
        )

        # Limit goals based on configured maximum
        return goals[:DISPLAY_LIMITS['max_goals']]

    def _build_year_end_review(
        self,
        collection: CollectionResult,
        highlights: List[str],
        awards: List[str],
    ) -> YearEndReview:
        """Generate year-end specific review content based on actual data."""
        return YearEndReview(
            proudest_moments=self._extract_proudest_moments(collection),
            biggest_challenges=self._extract_biggest_challenges(collection),
            lessons_learned=self._extract_lessons_learned(collection),
            next_year_goals=self._extract_next_year_goals(collection),
        )
