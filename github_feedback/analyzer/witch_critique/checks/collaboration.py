"""Collaboration and issue tracking checker for witch critique."""

from __future__ import annotations

from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from github_feedback.models import CollectionResult, WitchCritiqueItem

from github_feedback.constants import CRITIQUE_THRESHOLDS
from github_feedback.models import WitchCritiqueItem


class CollaborationChecker:
    """Check collaboration and issue tracking practices."""

    @staticmethod
    def check_issue_tracking(collection, critiques: List[WitchCritiqueItem]) -> None:
        """Check issue tracking practices and add critique if insufficient."""
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

    @staticmethod
    def check_diversity(collection, critiques: List[WitchCritiqueItem]) -> None:
        """Check collaboration diversity and add critique if too isolated."""
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
