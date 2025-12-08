"""Review quality checker for witch critique."""

from __future__ import annotations

from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from github_feedback.models import CollectionResult, DetailedFeedbackSnapshot, WitchCritiqueItem

from github_feedback.constants import CRITIQUE_THRESHOLDS
from github_feedback.models import WitchCritiqueItem


class ReviewQualityChecker:
    """Check review quality and frequency."""

    @staticmethod
    def check(
        collection,
        detailed_feedback: Optional,
        critiques: List[WitchCritiqueItem]
    ) -> None:
        """Check review quality and frequency, add critique if insufficient."""
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
