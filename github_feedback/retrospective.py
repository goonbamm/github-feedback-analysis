"""Enhanced retrospective analysis for deep developer insights."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from .models import (
    CollaborationNetwork,
    DetailedFeedbackSnapshot,
    MetricSnapshot,
    MonthlyTrend,
    TechStackAnalysis,
)


@dataclass(slots=True)
class TimeComparison:
    """Comparison between two time periods for trend analysis."""

    metric_name: str
    current_value: float
    previous_value: float
    change_absolute: float  # current - previous
    change_percentage: float  # (change / previous) * 100
    direction: str  # "increasing", "decreasing", "stable"
    significance: str  # "major", "moderate", "minor"

    def to_dict(self) -> Dict[str, Any]:
        """Serialize time comparison."""
        return {
            "metric_name": self.metric_name,
            "current_value": self.current_value,
            "previous_value": self.previous_value,
            "change_absolute": self.change_absolute,
            "change_percentage": self.change_percentage,
            "direction": self.direction,
            "significance": self.significance,
        }


@dataclass(slots=True)
class BehaviorPattern:
    """Analysis of work behavior and productivity patterns."""

    pattern_type: str  # "productivity_peak", "burnout_risk", "consistent_growth"
    description: str
    evidence: List[str]
    impact: str  # "positive", "negative", "neutral"
    recommendation: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize behavior pattern."""
        return {
            "pattern_type": self.pattern_type,
            "description": self.description,
            "evidence": self.evidence,
            "impact": self.impact,
            "recommendation": self.recommendation,
        }


@dataclass(slots=True)
class LearningInsight:
    """Track learning trajectory and skill development."""

    domain: str  # "frontend", "backend", "devops", "testing"
    technologies: List[str]
    evidence_commits: int
    evidence_prs: int
    growth_indicators: List[str]
    expertise_level: str  # "exploring", "developing", "proficient", "expert"

    def to_dict(self) -> Dict[str, Any]:
        """Serialize learning insight."""
        return {
            "domain": self.domain,
            "technologies": self.technologies,
            "evidence_commits": self.evidence_commits,
            "evidence_prs": evidence_prs,
            "growth_indicators": self.growth_indicators,
            "expertise_level": self.expertise_level,
        }


@dataclass(slots=True)
class ImpactAssessment:
    """Assess the business and team impact of contributions."""

    category: str  # "bug_fixes", "features", "refactoring", "documentation"
    contribution_count: int
    estimated_impact: str  # "high", "medium", "low"
    impact_description: str
    key_achievements: List[str]
    metrics: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize impact assessment."""
        return {
            "category": self.category,
            "contribution_count": self.contribution_count,
            "estimated_impact": self.estimated_impact,
            "impact_description": self.impact_description,
            "key_achievements": self.key_achievements,
            "metrics": self.metrics,
        }


@dataclass(slots=True)
class CollaborationInsight:
    """Deep analysis of collaboration patterns and team dynamics."""

    collaboration_strength: str  # "strong", "moderate", "developing"
    key_partnerships: List[Tuple[str, int, str]]  # (person, count, relationship_type)
    collaboration_quality: str  # Assessment of review depth and feedback quality
    knowledge_sharing: Dict[str, Any]  # Areas where developer shared knowledge
    mentorship_indicators: List[str]
    improvement_areas: List[str]

    def to_dict(self) -> Dict[str, Any]:
        """Serialize collaboration insight."""
        return {
            "collaboration_strength": self.collaboration_strength,
            "key_partnerships": [
                {"person": p, "count": c, "type": t} for p, c, t in self.key_partnerships
            ],
            "collaboration_quality": self.collaboration_quality,
            "knowledge_sharing": self.knowledge_sharing,
            "mentorship_indicators": self.mentorship_indicators,
            "improvement_areas": self.improvement_areas,
        }


@dataclass(slots=True)
class BalanceMetrics:
    """Work-life balance and sustainability indicators."""

    activity_variance: float  # 0-1, lower is more consistent
    burnout_risk_level: str  # "low", "moderate", "high"
    burnout_indicators: List[str]
    sustainability_score: float  # 0-100
    health_recommendations: List[str]
    positive_patterns: List[str]

    def to_dict(self) -> Dict[str, Any]:
        """Serialize balance metrics."""
        return {
            "activity_variance": self.activity_variance,
            "burnout_risk_level": self.burnout_risk_level,
            "burnout_indicators": self.burnout_indicators,
            "sustainability_score": self.sustainability_score,
            "health_recommendations": self.health_recommendations,
            "positive_patterns": self.positive_patterns,
        }


@dataclass(slots=True)
class BlockerAnalysis:
    """Identify blockers and friction points in the development process."""

    bottleneck_areas: List[str]
    long_pr_review_times: List[Dict[str, Any]]  # PRs that took unusually long
    stale_prs: int  # PRs that weren't merged or took very long
    improvement_velocity: float  # Time from PR open to merge (avg days)
    friction_points: List[str]
    process_recommendations: List[str]

    def to_dict(self) -> Dict[str, Any]:
        """Serialize blocker analysis."""
        return {
            "bottleneck_areas": self.bottleneck_areas,
            "long_pr_review_times": self.long_pr_review_times,
            "stale_prs": self.stale_prs,
            "improvement_velocity": self.improvement_velocity,
            "friction_points": self.friction_points,
            "process_recommendations": self.process_recommendations,
        }


@dataclass(slots=True)
class CodeHealthAnalysis:
    """Analyze technical debt and code health trends."""

    refactoring_ratio: float  # % of commits that are refactoring
    test_coverage_trend: str  # "improving", "stable", "declining"
    technical_debt_indicators: List[str]
    code_quality_trends: List[str]
    maintenance_burden: str  # "low", "moderate", "high"
    quality_improvement_suggestions: List[str]

    def to_dict(self) -> Dict[str, Any]:
        """Serialize code health analysis."""
        return {
            "refactoring_ratio": self.refactoring_ratio,
            "test_coverage_trend": self.test_coverage_trend,
            "technical_debt_indicators": self.technical_debt_indicators,
            "code_quality_trends": self.code_quality_trends,
            "maintenance_burden": self.maintenance_burden,
            "quality_improvement_suggestions": self.quality_improvement_suggestions,
        }


@dataclass(slots=True)
class ActionableInsight:
    """Concrete, actionable recommendations for improvement."""

    category: str  # "skills", "process", "collaboration", "balance"
    priority: str  # "high", "medium", "low"
    title: str
    description: str
    why_it_matters: str  # The reasoning behind this insight
    concrete_actions: List[str]  # Specific steps to take
    expected_outcome: str
    measurement: str  # How to measure success

    def to_dict(self) -> Dict[str, Any]:
        """Serialize actionable insight."""
        return {
            "category": self.category,
            "priority": self.priority,
            "title": self.title,
            "description": self.description,
            "why_it_matters": self.why_it_matters,
            "concrete_actions": self.concrete_actions,
            "expected_outcome": self.expected_outcome,
            "measurement": self.measurement,
        }


@dataclass(slots=True)
class RetrospectiveSnapshot:
    """Comprehensive retrospective analysis with deep insights."""

    # Period information
    period_description: str
    analysis_date: datetime

    # Comparative analysis
    time_comparisons: List[TimeComparison] = field(default_factory=list)

    # Behavioral and pattern analysis
    behavior_patterns: List[BehaviorPattern] = field(default_factory=list)
    learning_insights: List[LearningInsight] = field(default_factory=list)

    # Impact and value
    impact_assessments: List[ImpactAssessment] = field(default_factory=list)

    # Collaboration deep dive
    collaboration_insights: Optional[CollaborationInsight] = None

    # Sustainability and health
    balance_metrics: Optional[BalanceMetrics] = None

    # Process improvements
    blocker_analysis: Optional[BlockerAnalysis] = None
    code_health: Optional[CodeHealthAnalysis] = None

    # Actionable recommendations
    actionable_insights: List[ActionableInsight] = field(default_factory=list)

    # Narrative synthesis
    executive_summary: str = ""  # High-level overview
    key_wins: List[str] = field(default_factory=list)  # Top 3-5 achievements
    areas_for_growth: List[str] = field(default_factory=list)  # Top 3-5 opportunities
    retrospective_narrative: List[str] = field(default_factory=list)  # Story format

    def to_dict(self) -> Dict[str, Any]:
        """Serialize retrospective snapshot."""
        return {
            "period_description": self.period_description,
            "analysis_date": self.analysis_date.isoformat(),
            "time_comparisons": [tc.to_dict() for tc in self.time_comparisons],
            "behavior_patterns": [bp.to_dict() for bp in self.behavior_patterns],
            "learning_insights": [li.to_dict() for li in self.learning_insights],
            "impact_assessments": [ia.to_dict() for ia in self.impact_assessments],
            "collaboration_insights": (
                self.collaboration_insights.to_dict() if self.collaboration_insights else None
            ),
            "balance_metrics": self.balance_metrics.to_dict() if self.balance_metrics else None,
            "blocker_analysis": (
                self.blocker_analysis.to_dict() if self.blocker_analysis else None
            ),
            "code_health": self.code_health.to_dict() if self.code_health else None,
            "actionable_insights": [ai.to_dict() for ai in self.actionable_insights],
            "executive_summary": self.executive_summary,
            "key_wins": self.key_wins,
            "areas_for_growth": self.areas_for_growth,
            "retrospective_narrative": self.retrospective_narrative,
        }


@dataclass(slots=True)
class RetrospectiveAnalyzer:
    """Analyze metrics and generate comprehensive retrospective insights."""

    def analyze(self, metrics: MetricSnapshot) -> RetrospectiveSnapshot:
        """Generate comprehensive retrospective analysis from metrics."""
        retrospective = RetrospectiveSnapshot(
            period_description=f"{metrics.months}개월 ({metrics.since_date.strftime('%Y-%m-%d')} ~ {metrics.until_date.strftime('%Y-%m-%d')})",
            analysis_date=datetime.now(),
        )

        # Analyze time trends and comparisons
        retrospective.time_comparisons = self._analyze_time_comparisons(metrics)

        # Analyze behavior patterns
        retrospective.behavior_patterns = self._analyze_behavior_patterns(metrics)

        # Analyze learning trajectory
        retrospective.learning_insights = self._analyze_learning_insights(
            metrics.tech_stack, metrics.monthly_trends
        )

        # Assess impact
        retrospective.impact_assessments = self._assess_impact(metrics)

        # Deep dive into collaboration
        retrospective.collaboration_insights = self._analyze_collaboration(
            metrics.collaboration, metrics.detailed_feedback
        )

        # Analyze work-life balance
        retrospective.balance_metrics = self._analyze_balance(metrics.monthly_trends)

        # Identify blockers and friction
        retrospective.blocker_analysis = self._analyze_blockers(metrics)

        # Analyze code health
        retrospective.code_health = self._analyze_code_health(metrics)

        # Generate actionable insights
        retrospective.actionable_insights = self._generate_actionable_insights(retrospective)

        # Synthesize narrative
        retrospective.executive_summary = self._create_executive_summary(retrospective, metrics)
        retrospective.key_wins = self._identify_key_wins(retrospective, metrics)
        retrospective.areas_for_growth = self._identify_growth_areas(retrospective, metrics)
        retrospective.retrospective_narrative = self._create_narrative(retrospective, metrics)

        return retrospective

    def _analyze_time_comparisons(self, metrics: MetricSnapshot) -> List[TimeComparison]:
        """Compare current period with previous period to identify trends."""
        comparisons = []

        if not metrics.monthly_trends or len(metrics.monthly_trends) < 2:
            return comparisons

        # Split into two halves for comparison
        mid_point = len(metrics.monthly_trends) // 2
        first_half = metrics.monthly_trends[:mid_point]
        second_half = metrics.monthly_trends[mid_point:]

        def calculate_average(trends: List[MonthlyTrend], attr: str) -> float:
            values = [getattr(t, attr) for t in trends]
            return sum(values) / len(values) if values else 0.0

        # Compare commits
        prev_commits = calculate_average(first_half, "commits")
        curr_commits = calculate_average(second_half, "commits")
        comparisons.append(
            self._create_comparison("월평균 커밋", curr_commits, prev_commits)
        )

        # Compare PRs
        prev_prs = calculate_average(first_half, "pull_requests")
        curr_prs = calculate_average(second_half, "pull_requests")
        comparisons.append(self._create_comparison("월평균 PR", curr_prs, prev_prs))

        # Compare reviews
        prev_reviews = calculate_average(first_half, "reviews")
        curr_reviews = calculate_average(second_half, "reviews")
        comparisons.append(
            self._create_comparison("월평균 리뷰", curr_reviews, prev_reviews)
        )

        return comparisons

    def _create_comparison(
        self, name: str, current: float, previous: float
    ) -> TimeComparison:
        """Create a time comparison object."""
        change = current - previous
        change_pct = (change / previous * 100) if previous > 0 else 0.0

        if change > 0:
            direction = "increasing"
        elif change < 0:
            direction = "decreasing"
        else:
            direction = "stable"

        # Determine significance
        abs_change_pct = abs(change_pct)
        if abs_change_pct > 50:
            significance = "major"
        elif abs_change_pct > 20:
            significance = "moderate"
        else:
            significance = "minor"

        return TimeComparison(
            metric_name=name,
            current_value=current,
            previous_value=previous,
            change_absolute=change,
            change_percentage=change_pct,
            direction=direction,
            significance=significance,
        )

    def _analyze_behavior_patterns(self, metrics: MetricSnapshot) -> List[BehaviorPattern]:
        """Identify work behavior patterns from activity data."""
        patterns = []

        if not metrics.monthly_trends:
            return patterns

        # Calculate activity consistency
        monthly_totals = [
            t.commits + t.pull_requests + t.reviews + t.issues
            for t in metrics.monthly_trends
        ]
        avg_activity = sum(monthly_totals) / len(monthly_totals) if monthly_totals else 0
        variance = (
            sum((x - avg_activity) ** 2 for x in monthly_totals) / len(monthly_totals)
            if monthly_totals
            else 0
        )
        std_dev = variance**0.5

        # Pattern: Consistent activity
        if std_dev < avg_activity * 0.3:
            patterns.append(
                BehaviorPattern(
                    pattern_type="consistent_growth",
                    description="꾸준하고 일관된 활동 패턴을 보이고 있습니다",
                    evidence=[
                        f"월평균 활동: {avg_activity:.1f}건",
                        f"표준편차: {std_dev:.1f} (변동성 낮음)",
                    ],
                    impact="positive",
                    recommendation="현재의 페이스를 유지하면서 새로운 도전 과제를 추가해보세요",
                )
            )

        # Pattern: High variance (potential burnout risk)
        if std_dev > avg_activity * 0.5:
            high_months = [
                t.month for t, total in zip(metrics.monthly_trends, monthly_totals) if total > avg_activity * 1.5
            ]
            patterns.append(
                BehaviorPattern(
                    pattern_type="burnout_risk",
                    description="활동량의 큰 변동이 감지되었습니다",
                    evidence=[
                        f"고활동 월: {', '.join(high_months[:3])}",
                        f"변동성이 평균의 {(std_dev / avg_activity * 100):.0f}%",
                    ],
                    impact="negative",
                    recommendation="지속 가능한 페이스를 위해 업무량을 더 균등하게 분배하는 것을 고려해보세요",
                )
            )

        # Pattern: Growth trajectory
        if len(monthly_totals) >= 3:
            recent_avg = sum(monthly_totals[-3:]) / 3
            early_avg = sum(monthly_totals[:3]) / 3
            if recent_avg > early_avg * 1.2:
                patterns.append(
                    BehaviorPattern(
                        pattern_type="productivity_peak",
                        description="최근 생산성이 크게 향상되었습니다",
                        evidence=[
                            f"초기 평균: {early_avg:.1f}건/월",
                            f"최근 평균: {recent_avg:.1f}건/월",
                            f"증가율: {((recent_avg - early_avg) / early_avg * 100):.0f}%",
                        ],
                        impact="positive",
                        recommendation="이 성장세를 유지하되, 번아웃에 주의하세요",
                    )
                )

        return patterns

    def _analyze_learning_insights(
        self, tech_stack: Optional[TechStackAnalysis], monthly_trends: List[MonthlyTrend]
    ) -> List[LearningInsight]:
        """Track learning trajectory and skill development."""
        insights = []

        if not tech_stack or not tech_stack.top_languages:
            return insights

        # Analyze technology diversity
        if tech_stack.diversity_score > 0.6:
            insights.append(
                LearningInsight(
                    domain="다양한 기술 스택",
                    technologies=tech_stack.top_languages[:5],
                    evidence_commits=sum(tech_stack.languages.values()),
                    evidence_prs=0,  # Would need PR data to calculate
                    growth_indicators=[
                        f"{len(tech_stack.languages)}개의 서로 다른 언어 사용",
                        f"다양성 점수: {tech_stack.diversity_score:.2f}",
                    ],
                    expertise_level="proficient",
                )
            )

        # Analyze primary technology
        if tech_stack.top_languages:
            primary_lang = tech_stack.top_languages[0]
            primary_count = tech_stack.languages.get(primary_lang, 0)
            total_files = sum(tech_stack.languages.values())
            primary_ratio = primary_count / total_files if total_files > 0 else 0

            if primary_ratio > 0.5:
                expertise_level = "expert" if primary_ratio > 0.7 else "proficient"
                insights.append(
                    LearningInsight(
                        domain=f"{primary_lang} 전문성",
                        technologies=[primary_lang],
                        evidence_commits=primary_count,
                        evidence_prs=0,
                        growth_indicators=[
                            f"전체 작업의 {primary_ratio * 100:.0f}% 차지",
                            f"{primary_count}개 파일 변경",
                        ],
                        expertise_level=expertise_level,
                    )
                )

        return insights

    def _assess_impact(self, metrics: MetricSnapshot) -> List[ImpactAssessment]:
        """Assess the business and team impact of contributions."""
        assessments = []

        # Assess commit impact
        total_commits = metrics.stats.get("commits", {}).get("total", 0)
        if total_commits > 0:
            impact_level = "high" if total_commits > 200 else "medium" if total_commits > 50 else "low"
            assessments.append(
                ImpactAssessment(
                    category="코드 기여",
                    contribution_count=int(total_commits),
                    estimated_impact=impact_level,
                    impact_description=f"총 {total_commits:,}개의 커밋으로 코드베이스 발전에 기여",
                    key_achievements=[
                        f"월평균 {total_commits / metrics.months:.1f}개의 커밋으로 꾸준한 기여",
                    ],
                    metrics={"commits_per_month": total_commits / metrics.months},
                )
            )

        # Assess PR impact
        total_prs = metrics.stats.get("pull_requests", {}).get("total", 0)
        if total_prs > 0:
            impact_level = "high" if total_prs > 50 else "medium" if total_prs > 20 else "low"
            assessments.append(
                ImpactAssessment(
                    category="기능 개발",
                    contribution_count=int(total_prs),
                    estimated_impact=impact_level,
                    impact_description=f"{total_prs}개의 Pull Request로 새로운 기능과 개선사항 제공",
                    key_achievements=[
                        f"평균 월 {total_prs / metrics.months:.1f}개의 PR로 지속적인 가치 제공",
                    ],
                    metrics={"prs_per_month": total_prs / metrics.months},
                )
            )

        # Assess review impact
        total_reviews = metrics.stats.get("reviews", {}).get("total", 0)
        if total_reviews > 0:
            impact_level = "high" if total_reviews > 100 else "medium" if total_reviews > 30 else "low"
            assessments.append(
                ImpactAssessment(
                    category="코드 리뷰",
                    contribution_count=int(total_reviews),
                    estimated_impact=impact_level,
                    impact_description=f"{total_reviews}건의 리뷰로 팀 코드 품질 향상에 기여",
                    key_achievements=[
                        f"월평균 {total_reviews / metrics.months:.1f}건의 리뷰로 팀 지식 공유",
                    ],
                    metrics={"reviews_per_month": total_reviews / metrics.months},
                )
            )

        return assessments

    def _analyze_collaboration(
        self,
        collaboration: Optional[CollaborationNetwork],
        feedback: Optional[DetailedFeedbackSnapshot],
    ) -> Optional[CollaborationInsight]:
        """Deep analysis of collaboration patterns."""
        if not collaboration:
            return None

        # Determine collaboration strength
        if collaboration.unique_collaborators > 10:
            strength = "strong"
        elif collaboration.unique_collaborators > 5:
            strength = "moderate"
        else:
            strength = "developing"

        # Identify key partnerships
        partnerships = [
            (reviewer, count, "핵심 협업자" if count > 10 else "협업자")
            for reviewer, count in list(collaboration.pr_reviewers.items())[:5]
        ]

        # Assess collaboration quality from review feedback
        quality_assessment = "건설적이고 협력적"
        if feedback and feedback.review_tone_feedback:
            constructive = feedback.review_tone_feedback.constructive_reviews
            total = feedback.review_tone_feedback.total_reviews
            if total > 0 and constructive / total > 0.8:
                quality_assessment = "매우 건설적이고 협력적"

        # Knowledge sharing indicators
        knowledge_sharing = {
            "review_count": collaboration.review_received_count,
            "collaborators": collaboration.unique_collaborators,
            "engagement": "high" if collaboration.review_received_count > 50 else "moderate",
        }

        # Mentorship indicators
        mentorship_indicators = []
        if collaboration.review_received_count > 100:
            mentorship_indicators.append("높은 리뷰 활동으로 팀 멘토링 가능성")
        if collaboration.unique_collaborators > 10:
            mentorship_indicators.append("다양한 팀원과의 협업으로 지식 전파")

        # Improvement areas
        improvement_areas = []
        if collaboration.unique_collaborators < 5:
            improvement_areas.append("더 많은 팀원과 협업 기회 확대")
        if collaboration.review_received_count < 20:
            improvement_areas.append("코드 리뷰 참여도 증가")

        return CollaborationInsight(
            collaboration_strength=strength,
            key_partnerships=partnerships,
            collaboration_quality=quality_assessment,
            knowledge_sharing=knowledge_sharing,
            mentorship_indicators=mentorship_indicators,
            improvement_areas=improvement_areas,
        )

    def _analyze_balance(self, monthly_trends: List[MonthlyTrend]) -> Optional[BalanceMetrics]:
        """Analyze work-life balance and sustainability."""
        if not monthly_trends:
            return None

        # Calculate activity variance
        monthly_totals = [
            t.commits + t.pull_requests + t.reviews + t.issues for t in monthly_trends
        ]
        avg = sum(monthly_totals) / len(monthly_totals) if monthly_totals else 0
        variance = (
            sum((x - avg) ** 2 for x in monthly_totals) / len(monthly_totals)
            if monthly_totals
            else 0
        )
        normalized_variance = (variance**0.5) / avg if avg > 0 else 0

        # Assess burnout risk
        burnout_indicators = []
        if normalized_variance > 0.5:
            burnout_indicators.append("높은 활동량 변동성")
        if max(monthly_totals) > avg * 2:
            burnout_indicators.append("일부 월에 과도한 활동량")

        if len(burnout_indicators) >= 2:
            risk_level = "high"
        elif len(burnout_indicators) == 1:
            risk_level = "moderate"
        else:
            risk_level = "low"

        # Calculate sustainability score
        consistency_bonus = max(0, 50 - normalized_variance * 100)
        no_extreme_bonus = 50 if max(monthly_totals) < avg * 1.5 else 25
        sustainability_score = min(100, consistency_bonus + no_extreme_bonus)

        # Health recommendations
        recommendations = []
        if risk_level != "low":
            recommendations.append("업무량을 더 균등하게 분배하여 지속 가능성 향상")
        if normalized_variance < 0.3:
            recommendations.append("현재의 일관된 페이스 유지")

        # Positive patterns
        positive_patterns = []
        if risk_level == "low":
            positive_patterns.append("건강한 작업 패턴 유지")
        if normalized_variance < 0.3:
            positive_patterns.append("일관되고 지속 가능한 활동 수준")

        return BalanceMetrics(
            activity_variance=normalized_variance,
            burnout_risk_level=risk_level,
            burnout_indicators=burnout_indicators,
            sustainability_score=sustainability_score,
            health_recommendations=recommendations,
            positive_patterns=positive_patterns,
        )

    def _analyze_blockers(self, metrics: MetricSnapshot) -> Optional[BlockerAnalysis]:
        """Identify blockers and friction points."""
        # This would require PR timing data which we don't have in current metrics
        # Return a basic analysis for now
        return BlockerAnalysis(
            bottleneck_areas=[],
            long_pr_review_times=[],
            stale_prs=0,
            improvement_velocity=0.0,
            friction_points=[],
            process_recommendations=[
                "PR 리뷰 시간 데이터 수집을 통한 병목 지점 파악",
                "정기적인 프로세스 회고를 통한 개선점 발견",
            ],
        )

    def _analyze_code_health(self, metrics: MetricSnapshot) -> Optional[CodeHealthAnalysis]:
        """Analyze technical debt and code quality trends."""
        # Would need commit message analysis to detect refactoring
        # Return basic analysis for now

        refactoring_suggestions = []
        if metrics.detailed_feedback and metrics.detailed_feedback.commit_feedback:
            total_commits = metrics.detailed_feedback.commit_feedback.total_commits
            good_messages = metrics.detailed_feedback.commit_feedback.good_messages
            if total_commits > 0:
                quality_ratio = good_messages / total_commits
                if quality_ratio < 0.7:
                    refactoring_suggestions.append("커밋 메시지 품질 개선으로 코드 이력 관리 향상")

        return CodeHealthAnalysis(
            refactoring_ratio=0.0,  # Would need commit message parsing
            test_coverage_trend="stable",
            technical_debt_indicators=[],
            code_quality_trends=["지속적인 코드 리뷰로 품질 유지"],
            maintenance_burden="moderate",
            quality_improvement_suggestions=refactoring_suggestions,
        )

    def _generate_actionable_insights(
        self, retrospective: RetrospectiveSnapshot
    ) -> List[ActionableInsight]:
        """Generate concrete, actionable recommendations."""
        insights = []

        # Generate insights from behavior patterns
        for pattern in retrospective.behavior_patterns:
            if pattern.impact == "negative" and pattern.recommendation:
                insights.append(
                    ActionableInsight(
                        category="balance",
                        priority="high" if "burnout" in pattern.pattern_type else "medium",
                        title=pattern.description,
                        description=pattern.recommendation,
                        why_it_matters="지속 가능한 개발 속도를 유지하고 번아웃을 예방하기 위해",
                        concrete_actions=[
                            "주간 업무량 계획 시 최대 용량의 80%만 할당",
                            "고강도 업무 후 회복 시간 확보",
                            "정기적인 휴식과 재충전 시간 배정",
                        ],
                        expected_outcome="더 일관되고 지속 가능한 생산성",
                        measurement="월별 활동량의 표준편차 감소",
                    )
                )

        # Generate insights from learning trajectory
        for learning in retrospective.learning_insights:
            if learning.expertise_level in ["exploring", "developing"]:
                insights.append(
                    ActionableInsight(
                        category="skills",
                        priority="medium",
                        title=f"{learning.domain} 영역 전문성 강화",
                        description=f"{learning.domain}에서 더 깊은 전문성을 개발할 기회",
                        why_it_matters="핵심 역량을 강화하여 더 큰 영향력을 발휘하기 위해",
                        concrete_actions=[
                            "관련 기술의 고급 기능 학습",
                            "복잡한 문제 해결 경험 축적",
                            "해당 영역의 베스트 프랙티스 문서화",
                        ],
                        expected_outcome=f"{learning.domain} 영역의 팀 내 전문가로 성장",
                        measurement="관련 PR의 복잡도와 영향도 증가",
                    )
                )

        # Generate insights from collaboration
        if retrospective.collaboration_insights:
            for improvement in retrospective.collaboration_insights.improvement_areas:
                insights.append(
                    ActionableInsight(
                        category="collaboration",
                        priority="medium",
                        title="협업 범위 확대",
                        description=improvement,
                        why_it_matters="다양한 관점을 얻고 팀 전체의 지식을 향상시키기 위해",
                        concrete_actions=[
                            "새로운 팀원의 PR에 리뷰 참여",
                            "다른 팀/프로젝트와의 크로스 리뷰",
                            "페어 프로그래밍 세션 주도",
                        ],
                        expected_outcome="더 넓은 협업 네트워크와 지식 공유",
                        measurement="협업하는 동료 수 증가",
                    )
                )

        # Generate insights from code health
        if retrospective.code_health:
            for suggestion in retrospective.code_health.quality_improvement_suggestions:
                insights.append(
                    ActionableInsight(
                        category="process",
                        priority="medium",
                        title="코드 품질 개선",
                        description=suggestion,
                        why_it_matters="장기적인 유지보수성과 팀 생산성 향상을 위해",
                        concrete_actions=[
                            "커밋 전 자체 체크리스트 작성",
                            "의미 있는 커밋 메시지 작성 습관화",
                            "PR 템플릿 적극 활용",
                        ],
                        expected_outcome="더 명확한 코드 이력과 쉬운 유지보수",
                        measurement="커밋 메시지 품질 점수 향상",
                    )
                )

        # Sort by priority
        priority_order = {"high": 0, "medium": 1, "low": 2}
        insights.sort(key=lambda x: priority_order[x.priority])

        return insights[:10]  # Return top 10 insights

    def _create_executive_summary(
        self, retrospective: RetrospectiveSnapshot, metrics: MetricSnapshot
    ) -> str:
        """Create high-level executive summary."""
        parts = []

        # Period summary
        parts.append(f"**분석 기간**: {retrospective.period_description}")
        parts.append("")

        # Key metrics
        total_commits = metrics.stats.get("commits", {}).get("total", 0)
        total_prs = metrics.stats.get("pull_requests", {}).get("total", 0)
        total_reviews = metrics.stats.get("reviews", {}).get("total", 0)
        parts.append(
            f"이 기간 동안 **{total_commits}개의 커밋**, **{total_prs}개의 PR**, "
            f"**{total_reviews}건의 리뷰**로 활발한 기여를 이어갔습니다."
        )
        parts.append("")

        # Highlight trends
        if retrospective.time_comparisons:
            positive_trends = [
                tc for tc in retrospective.time_comparisons if tc.direction == "increasing"
            ]
            if positive_trends:
                trend = positive_trends[0]
                parts.append(
                    f"특히 **{trend.metric_name}**이(가) 전반기 대비 **{trend.change_percentage:.1f}% 증가**하여 "
                    f"지속적인 성장세를 보이고 있습니다."
                )
                parts.append("")

        # Behavior highlights
        if retrospective.behavior_patterns:
            positive_patterns = [p for p in retrospective.behavior_patterns if p.impact == "positive"]
            if positive_patterns:
                parts.append(f"**강점**: {positive_patterns[0].description}")
                parts.append("")

        # Balance check
        if retrospective.balance_metrics:
            if retrospective.balance_metrics.burnout_risk_level == "low":
                parts.append(
                    f"✅ **지속가능성 점수 {retrospective.balance_metrics.sustainability_score:.0f}점**으로 "
                    f"건강한 작업 패턴을 유지하고 있습니다."
                )
            elif retrospective.balance_metrics.burnout_risk_level == "high":
                parts.append(
                    f"⚠️ 번아웃 위험이 감지되었습니다. 업무량 조절이 필요합니다."
                )
            parts.append("")

        return "\n".join(parts)

    def _identify_key_wins(
        self, retrospective: RetrospectiveSnapshot, metrics: MetricSnapshot
    ) -> List[str]:
        """Identify top 3-5 key achievements."""
        wins = []

        # High-impact contributions
        high_impact = [ia for ia in retrospective.impact_assessments if ia.estimated_impact == "high"]
        for impact in high_impact[:2]:
            wins.append(f"{impact.category}: {impact.impact_description}")

        # Positive behavior patterns
        positive_patterns = [
            p for p in retrospective.behavior_patterns if p.impact == "positive"
        ][:2]
        for pattern in positive_patterns:
            wins.append(pattern.description)

        # Learning achievements
        expert_areas = [
            li for li in retrospective.learning_insights if li.expertise_level == "expert"
        ]
        for area in expert_areas[:1]:
            wins.append(f"{area.domain}에서 전문가 수준의 역량 입증")

        return wins[:5]

    def _identify_growth_areas(
        self, retrospective: RetrospectiveSnapshot, metrics: MetricSnapshot
    ) -> List[str]:
        """Identify top 3-5 areas for growth."""
        areas = []

        # High priority actionable insights
        high_priority = [ai for ai in retrospective.actionable_insights if ai.priority == "high"]
        for insight in high_priority[:3]:
            areas.append(insight.title)

        # Collaboration improvements
        if retrospective.collaboration_insights:
            for improvement in retrospective.collaboration_insights.improvement_areas[:2]:
                if improvement not in areas:
                    areas.append(improvement)

        # Balance concerns
        if retrospective.balance_metrics:
            if retrospective.balance_metrics.burnout_risk_level != "low":
                for indicator in retrospective.balance_metrics.burnout_indicators[:1]:
                    if indicator not in areas:
                        areas.append(f"작업 밸런스: {indicator}")

        return areas[:5]

    def _create_narrative(
        self, retrospective: RetrospectiveSnapshot, metrics: MetricSnapshot
    ) -> List[str]:
        """Create narrative-style retrospective story."""
        narrative = []

        # Opening: The journey
        total_commits = metrics.stats.get("commits", {}).get("total", 0)
        narrative.append(
            f"지난 {metrics.months}개월은 {total_commits}개의 커밋으로 채워진 성장의 여정이었습니다."
        )

        # Character: Your work style
        if retrospective.behavior_patterns:
            positive = [p for p in retrospective.behavior_patterns if p.impact == "positive"]
            if positive:
                narrative.append(f"{positive[0].description}")

        # Challenges: What you overcame
        if retrospective.balance_metrics and retrospective.balance_metrics.burnout_indicators:
            narrative.append(
                "도전적인 순간들도 있었지만, "
                + retrospective.balance_metrics.positive_patterns[0]
                if retrospective.balance_metrics.positive_patterns
                else "이를 극복하며 한층 성장했습니다"
            )

        # Growth: What you learned
        if retrospective.learning_insights:
            techs = ", ".join(retrospective.learning_insights[0].technologies[:3])
            narrative.append(f"{techs} 등의 기술을 통해 역량을 한층 더 발전시켰습니다.")

        # Impact: Your contribution
        if retrospective.impact_assessments:
            high_impact = [ia for ia in retrospective.impact_assessments if ia.estimated_impact == "high"]
            if high_impact:
                narrative.append(f"{high_impact[0].impact_description}")

        # Community: Collaboration
        if (
            retrospective.collaboration_insights
            and retrospective.collaboration_insights.collaboration_strength == "strong"
        ):
            narrative.append(
                f"{retrospective.collaboration_insights.key_partnerships.__len__()}명의 동료와 함께 "
                f"협업하며 팀의 성장에 기여했습니다."
            )

        # Closing: Looking forward
        narrative.append(
            "이러한 경험을 바탕으로 다음 단계로 나아갈 준비가 되었습니다."
        )

        return narrative


__all__ = [
    "TimeComparison",
    "BehaviorPattern",
    "LearningInsight",
    "ImpactAssessment",
    "CollaborationInsight",
    "BalanceMetrics",
    "BlockerAnalysis",
    "CodeHealthAnalysis",
    "ActionableInsight",
    "RetrospectiveSnapshot",
    "RetrospectiveAnalyzer",
]
