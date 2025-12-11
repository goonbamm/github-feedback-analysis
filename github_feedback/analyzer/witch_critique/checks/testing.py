"""Test coverage checker for witch critique."""

from __future__ import annotations

from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from github_feedback.core.models import CollectionResult, WitchCritiqueItem

from github_feedback.core.constants import CRITIQUE_THRESHOLDS
from github_feedback.core.models import WitchCritiqueItem


class TestingChecker:
    """Check test-related activity."""

    @staticmethod
    def check(collection, critiques: List[WitchCritiqueItem]) -> None:
        """Check test-related activity and add critique if insufficient."""
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
