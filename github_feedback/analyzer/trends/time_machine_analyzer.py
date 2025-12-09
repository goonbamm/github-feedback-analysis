"""Time machine analyzer for past vs present comparison."""

from __future__ import annotations

from typing import List, Optional

from github_feedback.models import (
    CollectionResult,
    PeriodComparison,
    TimeMachineComparison,
)


class TimeMachineAnalyzer:
    """Analyzer for comparing past and present performance."""

    @staticmethod
    def analyze(
        present_collection: CollectionResult,
        past_collection: Optional[CollectionResult] = None,
    ) -> Optional[TimeMachineComparison]:
        """Analyze time machine comparison between two periods.

        Args:
            present_collection: Recent period collection result
            past_collection: Earlier period collection result (if available)

        Returns:
            TimeMachineComparison or None if past data unavailable
        """
        if not past_collection:
            return None

        # Determine period labels
        present_label = f"최근 {present_collection.months}개월"
        past_label = f"{present_collection.months * 2}개월 전"

        # Build comparisons
        comparisons = TimeMachineAnalyzer._build_comparisons(
            past_collection, present_collection
        )

        # Generate insights
        overall_summary = TimeMachineAnalyzer._generate_overall_summary(comparisons)
        biggest_improvement = TimeMachineAnalyzer._find_biggest_improvement(comparisons)
        needs_attention = TimeMachineAnalyzer._find_needs_attention(comparisons)

        return TimeMachineComparison(
            past_period_label=past_label,
            present_period_label=present_label,
            comparisons=comparisons,
            overall_growth_summary=overall_summary,
            biggest_improvement=biggest_improvement,
            needs_attention=needs_attention,
        )

    @staticmethod
    def _build_comparisons(
        past: CollectionResult,
        present: CollectionResult,
    ) -> List[PeriodComparison]:
        """Build detailed comparisons for each metric.

        Args:
            past: Past period collection
            present: Present period collection

        Returns:
            List of PeriodComparison objects
        """
        comparisons = []

        # Commits comparison
        comparisons.append(TimeMachineAnalyzer._compare_metric(
            "커밋 수",
            past.commits,
            present.commits,
            "높을수록 좋음"
        ))

        # Pull requests comparison
        comparisons.append(TimeMachineAnalyzer._compare_metric(
            "PR 수",
            past.pull_requests,
            present.pull_requests,
            "높을수록 좋음"
        ))

        # Reviews comparison
        comparisons.append(TimeMachineAnalyzer._compare_metric(
            "리뷰 수",
            past.reviews,
            present.reviews,
            "높을수록 좋음"
        ))

        # Issues comparison
        comparisons.append(TimeMachineAnalyzer._compare_metric(
            "이슈 처리",
            past.issues,
            present.issues,
            "적절한 수준 유지"
        ))

        # Monthly velocity comparison
        past_velocity = past.commits / max(past.months, 1)
        present_velocity = present.commits / max(present.months, 1)
        comparisons.append(TimeMachineAnalyzer._compare_metric(
            "월평균 속도",
            past_velocity,
            present_velocity,
            "일관성 중요"
        ))

        # Collaboration score
        past_collab = (past.pull_requests + past.reviews) / max(past.months, 1)
        present_collab = (present.pull_requests + present.reviews) / max(present.months, 1)
        comparisons.append(TimeMachineAnalyzer._compare_metric(
            "협업 점수",
            past_collab,
            present_collab,
            "높을수록 좋음"
        ))

        return comparisons

    @staticmethod
    def _compare_metric(
        name: str,
        past_val: float,
        present_val: float,
        context: str = "",
    ) -> PeriodComparison:
        """Compare a single metric between two periods.

        Args:
            name: Metric name
            past_val: Past value
            present_val: Present value
            context: Additional context

        Returns:
            PeriodComparison object
        """
        # Calculate change percentage
        if past_val > 0:
            change_percent = ((present_val - past_val) / past_val) * 100
        else:
            change_percent = 100.0 if present_val > 0 else 0.0

        # Determine trend
        if abs(change_percent) < 5:
            trend = "stable"
        elif change_percent > 0:
            trend = "improving"
        else:
            trend = "declining"

        # Generate insight
        if trend == "improving":
            insight = f"✨ {abs(change_percent):.1f}% 증가! {context}"
        elif trend == "declining":
            insight = f"📉 {abs(change_percent):.1f}% 감소. {context}"
        else:
            insight = f"➡️ 안정적 유지. {context}"

        return PeriodComparison(
            metric_name=name,
            past_value=past_val,
            present_value=present_val,
            change_percent=change_percent,
            trend=trend,
            insight=insight,
        )

    @staticmethod
    def _generate_overall_summary(comparisons: List[PeriodComparison]) -> str:
        """Generate overall growth summary.

        Args:
            comparisons: List of period comparisons

        Returns:
            Summary string
        """
        improving_count = sum(1 for c in comparisons if c.trend == "improving")
        declining_count = sum(1 for c in comparisons if c.trend == "declining")
        stable_count = sum(1 for c in comparisons if c.trend == "stable")

        if improving_count > declining_count:
            return f"🚀 전체적으로 성장하는 추세입니다! {improving_count}개 지표 향상, {declining_count}개 지표 하락"
        elif declining_count > improving_count:
            return f"⚠️ 일부 영역에서 관심이 필요합니다. {declining_count}개 지표 하락, {improving_count}개 지표 향상"
        else:
            return f"⚖️ 안정적인 활동을 유지하고 있습니다. {stable_count}개 지표 안정"

    @staticmethod
    def _find_biggest_improvement(comparisons: List[PeriodComparison]) -> str:
        """Find the metric with biggest improvement.

        Args:
            comparisons: List of period comparisons

        Returns:
            Description of biggest improvement
        """
        improving = [c for c in comparisons if c.trend == "improving"]

        if not improving:
            return "지속적인 개선 노력이 필요합니다."

        best = max(improving, key=lambda c: c.change_percent)
        return f"🏆 {best.metric_name}: {best.change_percent:.1f}% 증가로 가장 큰 성장!"

    @staticmethod
    def _find_needs_attention(comparisons: List[PeriodComparison]) -> str:
        """Find metrics that need attention.

        Args:
            comparisons: List of period comparisons

        Returns:
            Description of what needs attention
        """
        declining = [c for c in comparisons if c.trend == "declining"]

        if not declining:
            return "모든 영역이 양호합니다! 🎉"

        worst = min(declining, key=lambda c: c.change_percent)
        return f"💡 {worst.metric_name}: {abs(worst.change_percent):.1f}% 감소, 개선 기회"
