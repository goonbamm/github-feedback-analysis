"""Prediction analyzer for future activity forecasting."""

from __future__ import annotations

import random
from typing import List

from github_feedback.models import (
    CollectionResult,
    MonthlyTrend,
    PredictionInsights,
    PredictionItem,
)


class PredictionAnalyzer:
    """Analyzer for predicting future activity based on patterns."""

    @staticmethod
    def analyze(
        collection: CollectionResult,
        monthly_trends: List[MonthlyTrend],
    ) -> PredictionInsights:
        """Analyze patterns and generate predictions.

        Args:
            collection: Collection result
            monthly_trends: Monthly trend data

        Returns:
            PredictionInsights with predictions and challenges
        """
        # Generate predictions
        predictions = PredictionAnalyzer._generate_predictions(
            collection, monthly_trends
        )

        # Generate personalized challenges
        challenges = PredictionAnalyzer._generate_challenges(
            collection, monthly_trends
        )

        # Create motivational message
        motivational_msg = PredictionAnalyzer._generate_motivational_message(
            collection
        )

        return PredictionInsights(
            predictions=predictions,
            suggested_challenges=challenges,
            motivational_message=motivational_msg,
        )

    @staticmethod
    def _generate_predictions(
        collection: CollectionResult,
        monthly_trends: List[MonthlyTrend],
    ) -> List[PredictionItem]:
        """Generate activity predictions based on trends.

        Args:
            collection: Collection result
            monthly_trends: Monthly trend data

        Returns:
            List of prediction items
        """
        predictions = []

        if not monthly_trends or len(monthly_trends) < 2:
            return predictions

        # Calculate trend direction
        recent_months = monthly_trends[-3:] if len(monthly_trends) >= 3 else monthly_trends
        avg_recent_commits = sum(m.commits for m in recent_months) / len(recent_months)

        # Predict next month commits
        month_span = max(collection.months, 1)
        current_velocity = collection.commits / month_span

        # Simple linear trend prediction
        if len(recent_months) >= 2:
            trend_slope = (recent_months[-1].commits - recent_months[0].commits) / len(recent_months)
            predicted_commits = max(0, avg_recent_commits + trend_slope)
        else:
            predicted_commits = avg_recent_commits

        confidence = "Medium" if len(monthly_trends) >= 3 else "Low"

        predictions.append(PredictionItem(
            metric="월간 커밋 수",
            current_value=current_velocity,
            predicted_value=predicted_commits,
            timeframe="다음 달",
            confidence=confidence,
            reasoning=f"최근 {len(recent_months)}개월 평균 기반 예측"
        ))

        # Predict PR activity
        avg_recent_prs = sum(m.pull_requests for m in recent_months) / len(recent_months)
        current_pr_velocity = collection.pull_requests / month_span

        predictions.append(PredictionItem(
            metric="PR 생성 수",
            current_value=current_pr_velocity,
            predicted_value=avg_recent_prs,
            timeframe="다음 달",
            confidence=confidence,
            reasoning="최근 활동 패턴 유지 가정"
        ))

        # Predict review activity
        avg_recent_reviews = sum(m.reviews for m in recent_months) / len(recent_months)
        current_review_velocity = collection.reviews / month_span

        predictions.append(PredictionItem(
            metric="코드 리뷰 수",
            current_value=current_review_velocity,
            predicted_value=avg_recent_reviews,
            timeframe="다음 달",
            confidence=confidence,
            reasoning="협업 패턴 지속 가정"
        ))

        # Predict total activity
        predicted_total = predicted_commits + avg_recent_prs + avg_recent_reviews

        predictions.append(PredictionItem(
            metric="총 활동량",
            current_value=current_velocity + current_pr_velocity + current_review_velocity,
            predicted_value=predicted_total,
            timeframe="다음 달",
            confidence="High" if confidence == "Medium" else "Medium",
            reasoning="모든 활동 패턴 종합"
        ))

        return predictions

    @staticmethod
    def _generate_challenges(
        collection: CollectionResult,
        monthly_trends: List[MonthlyTrend],
    ) -> List[str]:
        """Generate personalized challenges based on current activity.

        Args:
            collection: Collection result
            monthly_trends: Monthly trend data

        Returns:
            List of challenge suggestions
        """
        challenges = []
        month_span = max(collection.months, 1)

        # Commit challenges
        commits_per_month = collection.commits / month_span
        if commits_per_month < 20:
            challenges.append("🎯 도전: 다음 달 20개 이상 커밋하기")
        elif commits_per_month < 50:
            challenges.append("🎯 도전: 월간 50개 커밋 달성하기")
        else:
            challenges.append("🎯 도전: 현재 속도 유지하며 품질 향상하기")

        # PR challenges
        prs_per_month = collection.pull_requests / month_span
        if prs_per_month < 5:
            challenges.append("🎯 도전: 주 1개 이상 PR 만들기")
        elif prs_per_month < 10:
            challenges.append("🎯 도전: 월간 10개 PR 달성하기")

        # Review challenges
        reviews_per_month = collection.reviews / month_span
        if reviews_per_month < prs_per_month:
            challenges.append("🎯 도전: PR 수만큼 리뷰 남기기")
        elif reviews_per_month < 20:
            challenges.append("🎯 도전: 월간 20개 리뷰 달성하기")

        # Consistency challenges
        if len(monthly_trends) >= 3:
            recent_commits = [m.commits for m in monthly_trends[-3:]]
            std_dev = (max(recent_commits) - min(recent_commits)) / (sum(recent_commits) / 3)
            if std_dev > 0.5:
                challenges.append("🎯 도전: 매월 일관된 활동량 유지하기")

        # Quality challenges
        if collection.pull_request_examples:
            avg_size = sum(pr.additions + pr.deletions for pr in collection.pull_request_examples) / len(collection.pull_request_examples)
            if avg_size > 300:
                challenges.append("🎯 도전: PR 크기를 200줄 이하로 줄이기")
            elif avg_size < 50:
                challenges.append("🎯 도전: 더 의미있는 크기의 PR 만들기")

        # Return max 5 challenges
        return challenges[:5]

    @staticmethod
    def _generate_motivational_message(collection: CollectionResult) -> str:
        """Generate personalized motivational message.

        Args:
            collection: Collection result

        Returns:
            Motivational message string
        """
        total_activity = collection.commits + collection.pull_requests + collection.reviews
        month_span = max(collection.months, 1)
        activity_per_month = total_activity / month_span

        messages = []

        if activity_per_month >= 50:
            messages.append(
                "🌟 놀라운 활동량입니다! 이 속도면 곧 레전드 개발자가 될 거예요!"
            )
        elif activity_per_month >= 30:
            messages.append(
                "💪 훌륭한 페이스입니다! 꾸준함이 곧 실력이 됩니다!"
            )
        elif activity_per_month >= 15:
            messages.append(
                "👍 좋은 시작입니다! 조금만 더 분발하면 더 큰 성장을 이룰 수 있어요!"
            )
        else:
            messages.append(
                "🌱 작은 발걸음도 의미 있습니다! 매일 조금씩 발전해나가세요!"
            )

        # Add specific encouragement
        if collection.reviews > collection.pull_requests * 2:
            messages.append("리뷰를 통한 팀 기여가 정말 인상적입니다!")
        elif collection.commits > 100:
            messages.append("커밋 수가 정말 놀랍네요!")
        elif collection.pull_requests > 50:
            messages.append("활발한 PR 활동이 멋집니다!")

        return " ".join(messages)
