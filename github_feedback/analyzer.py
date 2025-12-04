"""Metric calculation logic for GitHub feedback analysis."""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List, NamedTuple, Optional

from .award_strategies import AwardCalculator
from .console import Console
from .constants import (
    ACTIVITY_THRESHOLDS,
    COLLECTION_LIMITS,
    CONSISTENCY_THRESHOLDS,
    CRITIQUE_THRESHOLDS,
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
    PullRequestSummary,
    ReviewToneFeedback,
    IssueFeedback,
    MonthlyTrend,
    MonthlyTrendInsights,
    TechStackAnalysis,
    CollaborationNetwork,
    YearEndReview,
    PersonalDevelopmentAnalysis,
    StrengthPoint,
    ImprovementArea,
    GrowthIndicator,
    WitchCritique,
    WitchCritiqueItem,
)
from .retrospective import RetrospectiveAnalyzer

console = Console()


# ============================================================================
# Helper Classes for Analysis
# ============================================================================

class ActivityMessageBuilder:
    """Helper class for building activity-based messages with threshold checks."""

    @staticmethod
    def build_if_exceeds(
        value: int | float,
        threshold: int | float,
        message_template: str,
        *format_args
    ) -> Optional[str]:
        """Build a message if value exceeds threshold.

        Args:
            value: The value to check
            threshold: The threshold to compare against
            message_template: Template string with placeholders
            *format_args: Arguments to format the template

        Returns:
            Formatted message if value > threshold, None otherwise
        """
        if value > threshold:
            return message_template.format(*format_args)
        return None

    @staticmethod
    def build_messages_from_checks(
        checks: List[tuple[int | float, int | float, str, tuple]]
    ) -> List[str]:
        """Build messages from a list of threshold checks.

        Args:
            checks: List of (value, threshold, template, args) tuples

        Returns:
            List of messages where threshold was exceeded
        """
        messages = []
        for value, threshold, template, args in checks:
            msg = ActivityMessageBuilder.build_if_exceeds(value, threshold, template, *args)
            if msg:
                messages.append(msg)
        return messages


class InsightExtractor:
    """Helper class for extracting insights from PR collections."""

    @staticmethod
    def filter_prs_by_keywords(prs: list, keywords: list[str]) -> list:
        """Filter pull requests by keywords in their titles.

        Args:
            prs: List of pull requests to filter
            keywords: List of keywords to search for in titles (case-insensitive)

        Returns:
            Filtered list of pull requests
        """
        return [pr for pr in prs if any(kw in pr.title.lower() for kw in keywords)]

    @staticmethod
    def categorize_prs_by_keywords(prs: list, keyword_groups: dict[str, list[str]]) -> dict[str, list]:
        """Categorize pull requests by multiple keyword groups in a single pass.

        This is more efficient than calling filter_prs_by_keywords multiple times
        as it only iterates through the PRs once.

        Args:
            prs: List of pull requests to categorize
            keyword_groups: Dictionary mapping category names to keyword lists
                Example: {'doc': ['doc', 'readme'], 'test': ['test']}

        Returns:
            Dictionary mapping category names to filtered PR lists
        """
        # Initialize result dictionary with empty lists
        result = {category: [] for category in keyword_groups}

        # Single pass through all PRs
        for pr in prs:
            pr_title_lower = pr.title.lower()
            for category, keywords in keyword_groups.items():
                if any(kw in pr_title_lower for kw in keywords):
                    result[category].append(pr)

        return result

    @staticmethod
    def extract_keyword_based_insight(
        prs: list,
        keywords: list[str],
        threshold: int,
        message_template: str
    ) -> Optional[str]:
        """Extract insight based on keyword filtering and threshold check.

        Args:
            prs: List of pull requests
            keywords: Keywords to filter by
            threshold: Minimum count for insight
            message_template: Template for the insight message (with {count} placeholder)

        Returns:
            Formatted message if threshold exceeded, None otherwise
        """
        if not prs:
            return None

        filtered_prs = InsightExtractor.filter_prs_by_keywords(prs, keywords)
        if len(filtered_prs) > threshold:
            return message_template.format(count=len(filtered_prs))
        return None


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
        from github_feedback.constants import MONTHS_FOR_YEAR_DISPLAY, MONTHS_PER_YEAR
        if months >= MONTHS_FOR_YEAR_DISPLAY:
            years = months // MONTHS_PER_YEAR
            remaining_months = months % MONTHS_PER_YEAR
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
        year_end_review = self._build_year_end_review(collection, highlights, awards)

        # Generate witch's critique
        witch_critique = self._generate_witch_critique(collection, detailed_feedback)

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
            year_end_review=year_end_review,
            witch_critique=witch_critique,
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

    def _generate_witch_critique(
        self,
        collection: CollectionResult,
        detailed_feedback: Optional[DetailedFeedbackSnapshot] = None,
    ) -> WitchCritique:
        """Generate harsh but constructive critique from the witch.

        This method ALWAYS returns a WitchCritique object. Even when no specific
        issues are found, it provides general improvement suggestions to ensure
        the witch's critique is always present in the report.

        Args:
            collection: Collection of repository data
            detailed_feedback: Optional detailed feedback snapshot

        Returns:
            WitchCritique with harsh but productive feedback (always returns, never None)
        """
        critiques: List[WitchCritiqueItem] = []

        # Check various aspects of development practices
        self._check_commit_message_quality(detailed_feedback, critiques)
        self._check_pr_size(collection, critiques)
        self._check_pr_title_quality(detailed_feedback, critiques)
        self._check_review_quality(collection, detailed_feedback, critiques)
        self._check_activity_consistency(collection, critiques)
        self._check_documentation_culture(collection, critiques)
        self._check_test_coverage(collection, critiques)
        self._check_branch_management(collection, critiques)
        self._check_issue_tracking(collection, critiques)
        self._check_collaboration_diversity(collection, critiques)

        # If no specific critiques, add fallback so witch always appears
        if not critiques:
            critiques.append(self._get_random_general_critique(collection))

        # Create witch critique with opening and closing
        import random
        opening_curses = [
            "🔮 자, 수정 구슬을 들여다보니... 흠, 개선할 게 좀 보이는군.",
            "🔮 크리스탈 볼이 말하길... 너한테 할 말이 좀 있대.",
            "🔮 예언의 수정 구슬에 미래가 보여. 이대로면 내년에도 똑같은 실수 반복할 텐데?",
        ]

        closing_prophecies = [
            "💫 이 독설들을 무시하면 내년에도 똑같은 얘기 들을 거야. 하지만 하나씩만 고쳐도 훨씬 나아질 거라는 것도 보여. 선택은 네 몫이야.",
            "💫 마녀의 조언은 여기까지. 듣든 말든 너 맘이지만, 1년 후 더 나은 개발자가 되고 싶다면... 뭐, 알아서 해.",
            "💫 수정 구슬이 보여주는 미래: 이것들만 고치면 내년엔 꽤 괜찮은 개발자가 될 수 있어. 안 고치면? 그건 네가 더 잘 알겠지.",
        ]

        return WitchCritique(
            opening_curse=random.choice(opening_curses),
            critiques=critiques,
            closing_prophecy=random.choice(closing_prophecies)
        )

    def _check_commit_message_quality(
        self,
        detailed_feedback: Optional[DetailedFeedbackSnapshot],
        critiques: List[WitchCritiqueItem]
    ) -> None:
        """Check commit message quality and add critique if poor.

        Args:
            detailed_feedback: Optional detailed feedback snapshot
            critiques: List to append critique to if issues found
        """
        if not detailed_feedback or not detailed_feedback.commit_feedback:
            return

        commit_fb = detailed_feedback.commit_feedback
        if commit_fb.total_commits == 0:
            return

        poor_ratio = commit_fb.poor_messages / commit_fb.total_commits
        if poor_ratio > CRITIQUE_THRESHOLDS['poor_commit_ratio']:
            critiques.append(
                WitchCritiqueItem(
                    category="커밋 메시지",
                    severity="🔥 치명적",
                    critique=f"커밋 메시지의 {poor_ratio*100:.0f}%가 형편없어. '수정', 'fix', 'update' 같은 게 전부야? 6개월 후 너 자신도 뭘 고쳤는지 모를 텐데.",
                    evidence=f"{commit_fb.total_commits}개 커밋 중 {commit_fb.poor_messages}개가 불량",
                    consequence="나중에 버그 찾느라 git log 보면서 시간 낭비할 거야. 팀원들도 네 변경사항 이해 못 해.",
                    remedy="커밋 메시지에 '왜'를 담아. 'fix: 로그인 시 토큰 만료 체크 누락 수정' 이런 식으로."
                )
            )

    def _check_pr_size(
        self,
        collection: CollectionResult,
        critiques: List[WitchCritiqueItem]
    ) -> None:
        """Check PR size and add critique if too large.

        Args:
            collection: Collection of repository data
            critiques: List to append critique to if issues found
        """
        if not collection.pull_request_examples:
            return

        large_prs = [pr for pr in collection.pull_request_examples
                    if (pr.additions + pr.deletions) > CRITIQUE_THRESHOLDS['large_pr_lines']]

        if len(large_prs) > len(collection.pull_request_examples) * CRITIQUE_THRESHOLDS['large_pr_ratio']:
            avg_size = sum(pr.additions + pr.deletions for pr in collection.pull_request_examples) / len(collection.pull_request_examples)
            critiques.append(
                WitchCritiqueItem(
                    category="PR 크기",
                    severity="⚡ 심각",
                    critique=f"PR 하나에 평균 {avg_size:.0f}줄? 리뷰어들 괴롭히는 게 취미야? 큰 PR은 안 읽힌다는 거 몰라?",
                    evidence=f"{len(large_prs)}개 PR이 {CRITIQUE_THRESHOLDS['large_pr_lines']}줄 이상",
                    consequence="리뷰 품질 떨어지고, 버그 놓치고, 머지 충돌 지옥에 빠질 거야.",
                    remedy=f"PR은 {CRITIQUE_THRESHOLDS['recommended_pr_size']}줄 이하로. 큰 기능은 쪼개서 여러 PR로 나눠. Feature flag 써."
                )
            )

    def _check_pr_title_quality(
        self,
        detailed_feedback: Optional[DetailedFeedbackSnapshot],
        critiques: List[WitchCritiqueItem]
    ) -> None:
        """Check PR title quality and add critique if vague.

        Args:
            detailed_feedback: Optional detailed feedback snapshot
            critiques: List to append critique to if issues found
        """
        if not detailed_feedback or not detailed_feedback.pr_title_feedback:
            return

        pr_fb = detailed_feedback.pr_title_feedback
        if pr_fb.total_prs == 0:
            return

        vague_ratio = pr_fb.vague_titles / pr_fb.total_prs
        if vague_ratio > CRITIQUE_THRESHOLDS['vague_title_ratio']:
            critiques.append(
                WitchCritiqueItem(
                    category="PR 제목",
                    severity="💀 위험",
                    critique=f"PR 제목 {vague_ratio*100:.0f}%가 뭔 말인지 모르겠어. '기능 추가', '버그 수정'? 어떤 기능? 어떤 버그?",
                    evidence=f"{pr_fb.total_prs}개 PR 중 {pr_fb.vague_titles}개가 모호함",
                    consequence="릴리스 노트 쓸 때 울고, 나중에 찾을 때 삽질하고.",
                    remedy="'feat: 사용자 프로필에 아바타 업로드 기능 추가' 이런 식으로 구체적으로."
                )
            )

    def _check_review_quality(
        self,
        collection: CollectionResult,
        detailed_feedback: Optional[DetailedFeedbackSnapshot],
        critiques: List[WitchCritiqueItem]
    ) -> None:
        """Check review quality and frequency, add critique if insufficient.

        Args:
            collection: Collection of repository data
            detailed_feedback: Optional detailed feedback snapshot
            critiques: List to append critique to if issues found
        """
        if detailed_feedback and detailed_feedback.review_tone_feedback:
            review_fb = detailed_feedback.review_tone_feedback
            if review_fb.total_reviews > 0:
                # Check if reviews are too short/neutral (may indicate low quality)
                low_quality_ratio = review_fb.neutral_reviews / review_fb.total_reviews
                if low_quality_ratio > CRITIQUE_THRESHOLDS['neutral_review_ratio']:
                    critiques.append(
                        WitchCritiqueItem(
                            category="코드 리뷰",
                            severity="🕷️ 경고",
                            critique=f"리뷰의 {low_quality_ratio*100:.0f}%가 그냥 'LGTM' 수준이야. 진짜 코드 읽긴 한 거야?",
                            evidence=f"{review_fb.total_reviews}개 리뷰 중 {review_fb.neutral_reviews}개가 형식적",
                            consequence="팀 코드 품질 떨어지고, 버그 프로덕션에서 발견되고.",
                            remedy="구체적인 피드백 줘. '이 함수 복잡도 높은데 테스트 추가하면 어때?' 이런 식으로."
                        )
                    )
        elif collection.reviews < collection.pull_requests * CRITIQUE_THRESHOLDS['review_pr_ratio']:
            # Not enough reviews compared to PRs
            critiques.append(
                WitchCritiqueItem(
                    category="코드 리뷰 참여",
                    severity="⚡ 심각",
                    critique=f"PR은 {collection.pull_requests}개인데 리뷰는 {collection.reviews}개? 남의 코드는 안 봐?",
                    evidence=f"PR 대비 리뷰 비율: {(collection.reviews/max(collection.pull_requests,1))*100:.0f}%",
                    consequence="팀에서 외톨이 되고, 네 PR도 리뷰 안 받게 될 거야.",
                    remedy="하루에 최소 2개 PR은 리뷰해. 남의 코드 보는 게 최고의 학습이야."
                )
            )

    def _check_activity_consistency(
        self,
        collection: CollectionResult,
        critiques: List[WitchCritiqueItem]
    ) -> None:
        """Check activity consistency and add critique if too sporadic.

        Args:
            collection: Collection of repository data
            critiques: List to append critique to if issues found
        """
        if collection.commits == 0 or collection.months == 0:
            return

        commits_per_month = collection.commits / collection.months
        if commits_per_month < CRITIQUE_THRESHOLDS['min_commits_per_month']:
            critiques.append(
                WitchCritiqueItem(
                    category="활동 일관성",
                    severity="🕷️ 경고",
                    critique=f"월평균 {commits_per_month:.1f}개 커밋? 며칠 몰아치고 쉬는 스타일이지? 개발은 마라톤이야, 단거리 달리기가 아니라.",
                    evidence=f"{collection.months}개월간 {collection.commits}개 커밋",
                    consequence="코드 품질 들쭉날쭉하고, 팀 협업 타이밍 안 맞고.",
                    remedy="매일 조금씩 꾸준히. 작은 커밋이라도 매일 하는 게 월말에 몰아치는 것보다 낫다."
                )
            )

    def _check_documentation_culture(
        self,
        collection: CollectionResult,
        critiques: List[WitchCritiqueItem]
    ) -> None:
        """Check documentation practices and add critique if insufficient.

        Args:
            collection: Collection of repository data
            critiques: List to append critique to if issues found
        """
        if not collection.pull_request_examples:
            return

        # Count documentation-related PRs
        doc_keywords = ['doc', 'readme', '문서', 'documentation', 'guide']
        doc_prs = [pr for pr in collection.pull_request_examples
                   if any(kw in pr.title.lower() for kw in doc_keywords)]

        doc_ratio = len(doc_prs) / len(collection.pull_request_examples)
        if doc_ratio < CRITIQUE_THRESHOLDS['min_doc_pr_ratio']:
            critiques.append(
                WitchCritiqueItem(
                    category="문서화",
                    severity="🕷️ 경고",
                    critique=f"문서 관련 PR이 전체의 {doc_ratio*100:.0f}%밖에 안 돼? 6개월 후 네 코드 이해 못 하는 건 너 자신이야.",
                    evidence=f"{len(collection.pull_request_examples)}개 PR 중 {len(doc_prs)}개만 문서 관련",
                    consequence="신규 팀원 온보딩 지옥, API 사용법 물어보는 슬랙 메시지 폭탄, 레거시 코드화 가속.",
                    remedy="README 업데이트, API 문서화, 아키텍처 다이어그램 추가. 코드만큼 문서도 중요해."
                )
            )

    def _check_test_coverage(
        self,
        collection: CollectionResult,
        critiques: List[WitchCritiqueItem]
    ) -> None:
        """Check test-related activity and add critique if insufficient.

        Args:
            collection: Collection of repository data
            critiques: List to append critique to if issues found
        """
        if not collection.pull_request_examples:
            return

        # Count test-related PRs
        test_keywords = ['test', '테스트', 'spec', 'unittest', 'integration']
        test_prs = [pr for pr in collection.pull_request_examples
                    if any(kw in pr.title.lower() for kw in test_keywords)]

        test_ratio = len(test_prs) / len(collection.pull_request_examples)
        if test_ratio < CRITIQUE_THRESHOLDS['min_test_pr_ratio']:
            critiques.append(
                WitchCritiqueItem(
                    category="테스트",
                    severity="⚡ 심각",
                    critique=f"테스트 관련 PR이 {test_ratio*100:.0f}%? 프로덕션이 네 테스트 환경이야? 대담한데?",
                    evidence=f"{len(collection.pull_request_examples)}개 PR 중 {len(test_prs)}개만 테스트 관련",
                    consequence="프로덕션 버그, 새벽 3시 긴급 배포, 사용자 이탈, 팀 신뢰도 추락.",
                    remedy="핵심 로직 테스트 작성, CI에 테스트 필수화, 커버리지 60% 목표. '돌아간다'로 만족하지 마."
                )
            )

    def _check_branch_management(
        self,
        collection: CollectionResult,
        critiques: List[WitchCritiqueItem]
    ) -> None:
        """Check branch management practices and add critique if messy.

        Args:
            collection: Collection of repository data
            critiques: List to append critique to if issues found
        """
        if not collection.pull_request_examples or collection.pull_requests == 0:
            return

        # Calculate average commits per PR
        avg_commits_per_pr = collection.commits / collection.pull_requests
        if avg_commits_per_pr > CRITIQUE_THRESHOLDS['max_commits_per_pr']:
            critiques.append(
                WitchCritiqueItem(
                    category="브랜치 관리",
                    severity="🕷️ 경고",
                    critique=f"PR당 평균 {avg_commits_per_pr:.1f}개 커밋? 브랜치에서 무슨 일이 벌어지는 거야? 정리 좀 해.",
                    evidence=f"{collection.commits}개 커밋 / {collection.pull_requests}개 PR",
                    consequence="리뷰어 혼란, 머지 충돌 지옥, Git 히스토리 난장판.",
                    remedy="기능별로 브랜치 분리, 작은 단위로 자주 PR, 리베이스로 커밋 정리. 깔끔한 히스토리가 프로야."
                )
            )

    def _check_issue_tracking(
        self,
        collection: CollectionResult,
        critiques: List[WitchCritiqueItem]
    ) -> None:
        """Check issue tracking practices and add critique if insufficient.

        Args:
            collection: Collection of repository data
            critiques: List to append critique to if issues found
        """
        if collection.commits == 0 and collection.pull_requests == 0:
            return

        total_activity = collection.commits + collection.pull_requests + collection.reviews
        if total_activity == 0:
            return

        issue_ratio = collection.issues / total_activity
        if issue_ratio < CRITIQUE_THRESHOLDS['min_issue_ratio']:
            critiques.append(
                WitchCritiqueItem(
                    category="이슈 추적",
                    severity="🕷️ 경고",
                    critique=f"전체 활동의 {issue_ratio*100:.0f}%만 이슈? 버그는 없어? 아니면 그냥 추적 안 하는 거야?",
                    evidence=f"총 {total_activity}건 활동 중 {collection.issues}건만 이슈",
                    consequence="버그 재발, 요구사항 추적 불가, 프로젝트 관리 실패, 우선순위 혼란.",
                    remedy="버그 발견하면 이슈 생성, 기능 요청도 이슈로 관리, 라벨링 체계화. 체계적인 추적이 프로젝트 성공의 열쇠야."
                )
            )

    def _check_collaboration_diversity(
        self,
        collection: CollectionResult,
        critiques: List[WitchCritiqueItem]
    ) -> None:
        """Check collaboration diversity and add critique if too isolated.

        Args:
            collection: Collection of repository data
            critiques: List to append critique to if issues found
        """
        # This check would ideally use collaboration data, but we can infer from PR/review ratio
        if collection.pull_requests == 0:
            return

        # If someone has many PRs but very few reviews, they might be working in isolation
        review_to_pr_ratio = collection.reviews / collection.pull_requests if collection.pull_requests > 0 else 0

        if review_to_pr_ratio < 0.3 and collection.pull_requests > 5:
            critiques.append(
                WitchCritiqueItem(
                    category="협업 다양성",
                    severity="🕷️ 경고",
                    critique=f"PR은 {collection.pull_requests}개인데 리뷰는 {collection.reviews}개? 혼자 섬에서 코딩하는 기분이야?",
                    evidence=f"PR 대비 리뷰 비율: {review_to_pr_ratio*100:.0f}%",
                    consequence="팀 내 지식 사일로, 코드 품질 저하, 버스 팩터 1, 외톨이 개발자.",
                    remedy="다양한 팀원과 협업, 정기적 코드 리뷰 참여, 페어 프로그래밍 시도. 혼자 잘해봤자 한계 있어."
                )
            )

    def _get_random_general_critique(self, collection: CollectionResult) -> WitchCritiqueItem:
        """Get a random general critique for developers with no specific issues.

        Args:
            collection: Collection of repository data for evidence text

        Returns:
            A randomly selected general improvement critique
        """
        import random

        general_critiques = [
            WitchCritiqueItem(
                category="개발자 성장",
                severity="💫 조언",
                critique="겉으로는 괜찮아 보이지만, 안주하면 퇴보하는 법이야. 지금이 딱 다음 레벨로 올라갈 때야.",
                evidence=f"총 {collection.commits}개 커밋, {collection.pull_requests}개 PR 분석 완료",
                consequence="현상 유지는 곧 뒤처지는 거야. 기술은 매일 발전하는데 너만 그 자리면?",
                remedy="새로운 기술 하나 배워봐. 오픈소스 기여하거나, 더 어려운 문제에 도전해봐."
            ),
            WitchCritiqueItem(
                category="코드 품질",
                severity="💫 조언",
                critique="코드는 일단 돌아가는데... 그냥 '돌아간다'로 만족할 거야? 아니면 '아름답게 돌아간다'를 목표로 할 거야?",
                evidence="커밋 히스토리 전체 분석 완료",
                consequence="동작하는 코드와 훌륭한 코드의 차이를 모르면, 영원히 시니어 개발자 못 돼.",
                remedy="리팩토링에 시간 투자해. 클린 코드 원칙 공부하고, 코드 리뷰에서 더 많이 배워."
            ),
            WitchCritiqueItem(
                category="협업 능력",
                severity="💫 조언",
                critique="혼자서는 잘하는데, 팀워크는 어때? 커뮤니케이션도 기술이야. 코딩만 잘한다고 다가 아니라고.",
                evidence=f"PR {collection.pull_requests}개, 리뷰 {collection.reviews}개 활동 확인",
                consequence="협업 못 하는 개발자는 혼자 할 수 있는 것만 할 수 있어. 큰 프로젝트는 무리.",
                remedy="PR 설명 더 자세히 써. 리뷰 댓글에 이유와 대안 제시해. 팀원들과 더 소통해."
            ),
            WitchCritiqueItem(
                category="학습 태도",
                severity="💫 조언",
                critique="익숙한 것만 반복하고 있지 않아? 편안함(comfort zone)에 머무르면 성장 없어.",
                evidence="활동 패턴 분석 완료",
                consequence="5년차인데 1년차 실력만 있는 개발자 되기 싫으면 변화 필요해.",
                remedy="매달 새로운 것 하나씩 시도해. 낯선 라이브러리, 다른 패러다임, 새로운 도구."
            ),
            WitchCritiqueItem(
                category="문서화",
                severity="💫 조언",
                critique="코드는 쓰는데 문서는? 6개월 후 네 코드 다시 볼 때 주석 없어서 후회하는 건 너야.",
                evidence="커밋 및 PR 패턴 분석",
                consequence="문서 없는 코드는 레거시가 되는 순간 아무도 못 건드려. 너도 못 건드리게 돼.",
                remedy="복잡한 로직에는 주석 달아. README 업데이트해. API는 문서화해."
            ),
            WitchCritiqueItem(
                category="테스트 문화",
                severity="💫 조언",
                critique="테스트 없이 코드 짜고 있는 건 아니겠지? '돌아가니까 됐지'는 초보 마인드야.",
                evidence="전체 개발 활동 검토",
                consequence="테스트 없는 리팩토링은 자살행위. 언젠가 배포하고 밤새 롤백하는 날 올 거야.",
                remedy="TDD는 아니어도, 핵심 로직은 테스트 작성해. Coverage 60% 이상 목표로."
            ),
        ]

        return random.choice(general_critiques)

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

    def _build_personal_development_analysis(self, analysis: Dict) -> PersonalDevelopmentAnalysis:
        """Build personal development analysis from LLM response."""
        # Parse strengths
        strengths = []
        for strength_data in analysis.get("strengths", []):
            if not isinstance(strength_data, dict):
                continue
            strengths.append(
                StrengthPoint(
                    category=strength_data.get("category", ""),
                    description=strength_data.get("description", ""),
                    evidence=strength_data.get("evidence", []),
                    impact=strength_data.get("impact", "medium"),
                )
            )

        # Parse improvement areas
        improvement_areas = []
        for improvement_data in analysis.get("improvement_areas", []):
            if not isinstance(improvement_data, dict):
                continue
            improvement_areas.append(
                ImprovementArea(
                    category=improvement_data.get("category", ""),
                    description=improvement_data.get("description", ""),
                    evidence=improvement_data.get("evidence", []),
                    suggestions=improvement_data.get("suggestions", []),
                    priority=improvement_data.get("priority", "medium"),
                )
            )

        # Parse growth indicators
        growth_indicators = []
        for growth_data in analysis.get("growth_indicators", []):
            if not isinstance(growth_data, dict):
                continue
            growth_indicators.append(
                GrowthIndicator(
                    aspect=growth_data.get("aspect", ""),
                    description=growth_data.get("description", ""),
                    before_examples=growth_data.get("before_examples", []),
                    after_examples=growth_data.get("after_examples", []),
                    progress_summary=growth_data.get("progress_summary", ""),
                )
            )

        return PersonalDevelopmentAnalysis(
            strengths=strengths,
            improvement_areas=improvement_areas,
            growth_indicators=growth_indicators,
            overall_assessment=analysis.get("overall_assessment", ""),
            key_achievements=analysis.get("key_achievements", []),
            next_focus_areas=analysis.get("next_focus_areas", []),
        )

    def build_detailed_feedback(
        self,
        commit_analysis: Optional[Dict] = None,
        pr_title_analysis: Optional[Dict] = None,
        review_tone_analysis: Optional[Dict] = None,
        issue_analysis: Optional[Dict] = None,
        personal_development_analysis: Optional[Dict] = None,
    ) -> DetailedFeedbackSnapshot:
        """Build detailed feedback snapshot from LLM analysis results."""

        return DetailedFeedbackSnapshot(
            commit_feedback=self._build_commit_feedback(commit_analysis) if commit_analysis else None,
            pr_title_feedback=self._build_pr_title_feedback(pr_title_analysis) if pr_title_analysis else None,
            review_tone_feedback=self._build_review_tone_feedback(review_tone_analysis) if review_tone_analysis else None,
            issue_feedback=self._build_issue_feedback(issue_analysis) if issue_analysis else None,
            personal_development=self._build_personal_development_analysis(personal_development_analysis) if personal_development_analysis else None,
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
        """Calculate trend direction from monthly activities.

        Algorithm:
        1. Requires minimum number of months (from TREND_THRESHOLDS)
        2. Splits activity data into two halves (early vs recent)
        3. Compares average activity between halves
        4. Returns 'increasing' if recent > early * multiplier
        5. Returns 'decreasing' if recent < early * multiplier
        6. Returns 'stable' otherwise

        Args:
            monthly_activities: List of (month, activity_count) tuples

        Returns:
            One of: "increasing", "decreasing", or "stable"
        """
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
        """Calculate consistency score from monthly activities.

        Uses coefficient of variation (CV) to measure consistency:
        - CV = standard_deviation / mean
        - Lower CV indicates more consistent activity
        - Returns score from 0 (highly variable) to 1 (perfectly consistent)
        """
        activities = [act for _, act in monthly_activities if act > 0]
        if not activities or len(activities) < 2:
            return 0.0

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

    def _calculate_pr_size(self, pr: PullRequest) -> int:
        """Calculate the total size of a pull request (additions + deletions).

        Args:
            pr: Pull request to calculate size for

        Returns:
            Total number of lines changed
        """
        return pr.additions + pr.deletions

    def _get_total_changes(self, prs: List[PullRequest]) -> int:
        """Calculate total changes across all pull requests.

        Args:
            prs: List of pull requests

        Returns:
            Sum of all additions and deletions
        """
        return sum(self._calculate_pr_size(pr) for pr in prs)

    def _find_largest_pr(self, prs: List[PullRequest]) -> PullRequest:
        """Find the pull request with the most changes.

        Args:
            prs: List of pull requests

        Returns:
            Pull request with the largest number of changes
        """
        return max(prs, key=self._calculate_pr_size)

    def _extract_proudest_moments(self, collection: CollectionResult) -> List[str]:
        """Extract proudest moments from collection data using helper."""
        # Define threshold checks for basic metrics
        basic_checks = [
            (collection.commits, ACTIVITY_THRESHOLDS['very_high_commits'],
             "총 {}회의 커밋으로 꾸준히 코드베이스를 개선했습니다.", (collection.commits,)),
            (collection.pull_requests, ACTIVITY_THRESHOLDS['very_high_prs'],
             "{}개의 Pull Request를 성공적으로 머지했습니다.", (collection.pull_requests,)),
            (collection.reviews, ACTIVITY_THRESHOLDS['very_high_reviews'],
             "{}회의 코드 리뷰로 팀의 코드 품질 향상에 기여했습니다.", (collection.reviews,)),
        ]

        moments = ActivityMessageBuilder.build_messages_from_checks(basic_checks)

        # Add insights from PR examples
        if collection.pull_request_examples:
            total_changes = self._get_total_changes(collection.pull_request_examples)
            msg = ActivityMessageBuilder.build_if_exceeds(
                total_changes,
                ACTIVITY_THRESHOLDS['very_large_pr'],
                "총 {:,}줄의 코드 변경으로 대규모 개선을 주도했습니다.",
                total_changes
            )
            if msg:
                moments.append(msg)

            # Find largest PR
            largest_pr = self._find_largest_pr(collection.pull_request_examples)
            largest_pr_size = self._calculate_pr_size(largest_pr)
            msg = ActivityMessageBuilder.build_if_exceeds(
                largest_pr_size,
                ACTIVITY_THRESHOLDS['large_pr'],
                "가장 큰 PR(#{}: {})에서 {:,}줄의 변경으로 도전적인 작업을 완수했습니다.",
                largest_pr.number, largest_pr.title, largest_pr_size
            )
            if msg:
                moments.append(msg)

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
            msg = InsightExtractor.extract_keyword_based_insight(
                collection.pull_request_examples,
                ['feature', 'feat', '기능', 'add'],
                ACTIVITY_THRESHOLDS['feature_pr_threshold'],
                "{count}개의 새로운 기능을 개발하며 요구사항 분석과 설계 능력을 향상시켰습니다."
            )
            if msg:
                challenges.append(msg)

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
            # Optimize: filter PRs in a single pass to avoid multiple iterations
            pr_categories = InsightExtractor.categorize_prs_by_keywords(
                collection.pull_request_examples,
                {
                    'doc': ['doc', 'readme', '문서'],
                    'test': ['test', '테스트']
                }
            )

            if len(pr_categories['doc']) < ACTIVITY_THRESHOLDS['moderate_doc_prs']:
                goals.append(
                    "문서화에 더 신경써서 프로젝트의 접근성과 유지보수성 향상하기"
                )

            if len(pr_categories['test']) < ACTIVITY_THRESHOLDS['moderate_test_prs']:
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
