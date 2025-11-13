"""Award calculation strategies for GitHub feedback analysis.

This module implements the Strategy pattern for award determination,
making it easier to add, remove, or modify award rules.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Dict, Tuple, Any

from .models import CollectionResult
from .constants import (
    AWARD_CONSISTENCY_THRESHOLDS,
    AWARD_BALANCED_THRESHOLDS,
    AWARD_PR_THRESHOLDS,
)


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
        (10, "🏃 스프린터 상 — 월 평균 10회 이상의 커밋으로 꾸준한 진전을 이뤘습니다."),
    ],
    "collaboration": [
        (20, "🤝 협업 마스터 상 — 월 평균 20회 이상의 PR과 리뷰로 팀워크의 중심이 되었습니다."),
        (10, "👥 협업 전문가 상 — 월 평균 10회 이상의 PR과 리뷰로 팀 시너지를 강화했습니다."),
        (5, "🤗 팀 플레이어 상 — 월 평균 5회 이상의 PR과 리뷰로 협업 문화에 기여했습니다."),
    ],
    "activity_consistency": [
        ((30, 6), "📅 꾸준함의 달인 상 — 6개월 이상 월 평균 30회 이상의 활동으로 일관성을 입증했습니다."),
        ((15, 3), "🔄 지속성 상 — 꾸준한 월별 활동으로 성실함을 보여줬습니다."),
    ],
    "change_scale": [
        (10000, "🌋 코드 화산 상 — 10000줄 이상의 폭발적인 변경으로 새로운 시대를 열었습니다."),
        (5000, "🏗️ 대규모 아키텍트 상 — 5000줄 이상의 변경으로 대담한 리팩터링을 완수했습니다."),
        (2000, "🔨 대형 빌더 상 — 2000줄 이상의 변경으로 큰 규모의 개선을 이뤄냈습니다."),
        (1000, "🏠 중형 건축가 상 — 1000줄 이상의 변경으로 의미있는 개선을 완료했습니다."),
    ],
    "review_dedication": [
        (3.0, "🔍 리뷰 매니아 상 — 자신의 PR보다 3배 이상 많은 리뷰로 팀 성장에 헌신했습니다."),
        (2.0, "👁️ 코드 감시자 상 — 자신의 PR보다 2배 이상 많은 리뷰로 품질 관리에 기여했습니다."),
    ],
}


class AwardStrategy(ABC):
    """Base class for award calculation strategies."""

    @abstractmethod
    def calculate(self, collection: CollectionResult) -> List[str]:
        """Calculate awards based on collection metrics.

        Args:
            collection: Collection of repository data

        Returns:
            List of award strings
        """
        pass


class TierBasedAwardStrategy(AwardStrategy):
    """Strategy for tier-based awards (commits, PRs, reviews, etc.)."""

    def calculate(self, collection: CollectionResult) -> List[str]:
        """Calculate tier-based awards."""
        awards = []
        month_span = max(collection.months, 1)

        # Direct metric awards
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

        # Large-scale change awards
        if collection.pull_request_examples:
            max_change = max(
                (pr.additions + pr.deletions for pr in collection.pull_request_examples),
                default=0
            )
            self._add_tier_award(awards, "change_scale", max_change)

        # Review dedication awards
        if collection.pull_requests > 0:
            review_ratio = collection.reviews / collection.pull_requests
            self._add_tier_award(awards, "review_dedication", review_ratio)

        return awards

    @staticmethod
    def _add_tier_award(awards: List[str], category: str, value: float) -> None:
        """Add tier-based award if value meets threshold."""
        if category not in AWARD_TIERS:
            return

        for threshold, award_text in AWARD_TIERS[category]:
            if value >= threshold:
                awards.append(award_text)
                break


class ActivityConsistencyAwardStrategy(AwardStrategy):
    """Strategy for activity consistency awards."""

    def calculate(self, collection: CollectionResult) -> List[str]:
        """Calculate activity consistency awards."""
        awards = []
        month_span = max(collection.months, 1)
        total_activity = collection.commits + collection.pull_requests + collection.reviews
        activity_per_month = total_activity / month_span

        # Activity consistency awards
        for (threshold_activity, threshold_months), award_text in AWARD_TIERS["activity_consistency"]:
            if activity_per_month >= threshold_activity and collection.months >= threshold_months:
                awards.append(award_text)
                break

        # Consistency king (매우 꾸준한 활동)
        if (collection.months >= AWARD_CONSISTENCY_THRESHOLDS['consistent_months'] and
            activity_per_month >= AWARD_CONSISTENCY_THRESHOLDS['consistent_activity_per_month']):
            awards.append(
                "👑 일관성의 왕 상 — 6개월 이상 월 20회 이상의 꾸준한 활동을 유지했습니다."
            )

        # Sprint finisher (최근 활동이 많은 경우)
        if collection.months >= AWARD_CONSISTENCY_THRESHOLDS['sprint_months']:
            velocity_score = collection.commits / month_span
            if velocity_score >= AWARD_CONSISTENCY_THRESHOLDS['sprint_velocity']:
                awards.append(
                    "🏁 스프린트 피니셔 상 — 높은 월평균 속도로 프로젝트를 빠르게 전진시켰습니다."
                )

        return awards


class BalancedContributorAwardStrategy(AwardStrategy):
    """Strategy for balanced contributor awards."""

    def calculate(self, collection: CollectionResult) -> List[str]:
        """Calculate balanced contributor awards."""
        awards = []
        total_activity = collection.commits + collection.pull_requests + collection.reviews

        # All-rounder award
        if (collection.commits >= AWARD_BALANCED_THRESHOLDS['allrounder_commits'] and
            collection.pull_requests >= AWARD_BALANCED_THRESHOLDS['allrounder_prs'] and
            collection.reviews >= AWARD_BALANCED_THRESHOLDS['allrounder_reviews']):
            awards.append(
                "🌟 다재다능 상 — 커밋, PR, 리뷰 전 영역에서 균형잡힌 기여를 보여줬습니다."
            )

        # Balanced contributor award
        if (collection.commits > 0 and collection.pull_requests > 0 and
            collection.reviews > 0 and total_activity > 0):
            commit_ratio = collection.commits / total_activity
            pr_ratio = collection.pull_requests / total_activity
            review_ratio = collection.reviews / total_activity

            # Check if all three are balanced (each between 20% and 50%)
            min_ratio = AWARD_BALANCED_THRESHOLDS['balanced_min_ratio']
            max_ratio = AWARD_BALANCED_THRESHOLDS['balanced_max_ratio']
            if all(min_ratio <= ratio <= max_ratio for ratio in [commit_ratio, pr_ratio, review_ratio]):
                awards.append(
                    "⚖️ 균형잡힌 기여자 상 — 커밋, PR, 리뷰를 완벽하게 균형있게 수행했습니다."
                )

        # Renaissance developer (모든 지표가 높음)
        if (collection.commits >= AWARD_BALANCED_THRESHOLDS['renaissance_commits'] and
            collection.pull_requests >= AWARD_BALANCED_THRESHOLDS['renaissance_prs'] and
            collection.reviews >= AWARD_BALANCED_THRESHOLDS['renaissance_reviews'] and
            collection.issues >= AWARD_BALANCED_THRESHOLDS['renaissance_issues']):
            awards.append(
                "🎭 르네상스 개발자 상 — 모든 영역에서 뛰어난 활약을 펼친 완벽한 올라운더입니다."
            )

        return awards


class PRCharacteristicAwardStrategy(AwardStrategy):
    """Strategy for PR characteristic-based awards."""

    def calculate(self, collection: CollectionResult) -> List[str]:
        """Calculate PR characteristic awards."""
        awards = []

        if not collection.pull_request_examples:
            return awards

        # Micro-commit artist award (많은 작은 PR)
        small_prs = sum(1 for pr in collection.pull_request_examples
                      if (pr.additions + pr.deletions) < AWARD_PR_THRESHOLDS['micro_pr_size'])
        if small_prs >= AWARD_PR_THRESHOLDS['micro_pr_count']:
            awards.append(
                "🎨 미세 조율 장인 상 — 10개 이상의 작은 PR로 점진적 개선의 미학을 보여줬습니다."
            )

        # Big bang award (큰 PR)
        huge_prs = sum(1 for pr in collection.pull_request_examples
                     if (pr.additions + pr.deletions) > 1000)
        if huge_prs >= 3:
            awards.append(
                "💥 빅뱅 상 — 3개 이상의 대규모 PR로 혁신적인 변화를 주도했습니다."
            )

        # Quick merger award (빠른 병합)
        quick_merges = sum(1 for pr in collection.pull_request_examples
                         if pr.merged_at and pr.created_at and
                         (pr.merged_at - pr.created_at).total_seconds() < 3600)
        if quick_merges >= 5:
            awards.append(
                "⚡ 스피드 머저 상 — 5개 이상의 PR을 1시간 내 병합하는 민첩함을 보여줬습니다."
            )

        # High PR merge rate
        if collection.pull_requests >= 20:
            merged_count = sum(1 for pr in collection.pull_request_examples if pr.merged_at)
            merge_rate = merged_count / len(collection.pull_request_examples)
            if merge_rate >= 0.9:
                awards.append(
                    "✅ 머지 마스터 상 — 90% 이상의 높은 PR 병합률로 탁월한 코드 품질을 입증했습니다."
                )

        return awards


class RoleBasedAwardStrategy(AwardStrategy):
    """Strategy for role-based awards (champion, machine, etc.)."""

    def calculate(self, collection: CollectionResult) -> List[str]:
        """Calculate role-based awards."""
        awards = []

        # Review champion (리뷰가 가장 많은 경우)
        if (collection.reviews > collection.commits and
            collection.reviews > collection.pull_requests and
            collection.reviews >= 30):
            awards.append(
                "👨‍🏫 리뷰 챔피언 상 — 다른 활동보다 리뷰에 집중하며 팀 성장의 멘토가 되었습니다."
            )

        # Commit machine (커밋이 압도적으로 많은 경우)
        if (collection.commits > collection.pull_requests * 3 and
            collection.commits > collection.reviews * 3 and
            collection.commits >= 100):
            awards.append(
                "🔥 커밋 머신 상 — 압도적인 커밋 수로 코드베이스의 핵심 동력이 되었습니다."
            )

        # Issue warrior award
        if collection.issues > collection.commits and collection.issues >= 30:
            awards.append(
                "🛠️ 이슈 전사 상 — 커밋보다 많은 이슈 처리로 프로젝트 안정성에 집중했습니다."
            )

        return awards


class QualityAwardStrategy(AwardStrategy):
    """Strategy for quality-based awards."""

    def calculate(self, collection: CollectionResult) -> List[str]:
        """Calculate quality-based awards."""
        awards = []

        # Stability award
        if collection.issues and collection.issues <= max(collection.commits // 6, 1):
            awards.append(
                "🛡️ 안정 지킴이 상 — 활동 대비 적은 이슈로 안정성을 지켰습니다."
            )

        # Quality guardian (이슈 대비 높은 리뷰)
        if collection.reviews >= 30 and collection.issues > 0:
            review_issue_ratio = collection.reviews / collection.issues
            if review_issue_ratio >= 3:
                awards.append(
                    "🎯 품질 수호자 상 — 이슈 대비 3배 이상의 리뷰로 사전 품질 관리에 힘썼습니다."
                )

        return awards


class ThemeBasedAwardStrategy(AwardStrategy):
    """Strategy for theme-based awards (docs, tests, refactor, etc.)."""

    def calculate(self, collection: CollectionResult) -> List[str]:
        """Calculate theme-based awards."""
        awards = []

        if not collection.pull_request_examples:
            return awards

        # Documentation hero
        doc_prs = sum(1 for pr in collection.pull_request_examples
                     if any(keyword in pr.title.lower()
                           for keyword in ['doc', 'readme', 'documentation', '문서']))
        if doc_prs >= 5:
            awards.append(
                "📚 문서화 영웅 상 — 5개 이상의 문서 PR로 지식 공유에 기여했습니다."
            )

        # Test advocate
        test_prs = sum(1 for pr in collection.pull_request_examples
                      if any(keyword in pr.title.lower()
                            for keyword in ['test', 'testing', '테스트', 'spec']))
        if test_prs >= 5:
            awards.append(
                "🧪 테스트 옹호자 상 — 5개 이상의 테스트 PR로 코드 안정성을 강화했습니다."
            )

        # Refactoring master
        refactor_prs = sum(1 for pr in collection.pull_request_examples
                          if any(keyword in pr.title.lower()
                                for keyword in ['refactor', 'refactoring', '리팩터링', 'cleanup', 'clean']))
        if refactor_prs >= 5:
            awards.append(
                "♻️ 리팩터링 마스터 상 — 5개 이상의 리팩터링 PR로 코드 품질을 향상시켰습니다."
            )

        # Bug squasher
        bug_prs = sum(1 for pr in collection.pull_request_examples
                     if any(keyword in pr.title.lower()
                           for keyword in ['fix', 'bug', 'hotfix', '버그', '수정']))
        if bug_prs >= 10:
            awards.append(
                "🐛 버그 스쿼셔 상 — 10개 이상의 버그 수정 PR로 안정성을 높였습니다."
            )

        # Feature factory
        feature_prs = sum(1 for pr in collection.pull_request_examples
                         if any(keyword in pr.title.lower()
                               for keyword in ['feature', 'feat', 'add', 'new', '추가', '기능']))
        if feature_prs >= 10:
            awards.append(
                "🏭 기능 공장 상 — 10개 이상의 기능 추가 PR로 제품을 풍부하게 만들었습니다."
            )

        return awards


class DefaultAwardStrategy(AwardStrategy):
    """Strategy for default award when no other awards are given."""

    def calculate(self, collection: CollectionResult) -> List[str]:
        """Return default award."""
        return [
            "🌱 성장 씨앗 상 — 작은 발걸음들이 모여 내일의 큰 성장을 준비하고 있습니다."
        ]


@dataclass(slots=True)
class AwardCalculator:
    """Orchestrates multiple award strategies to determine all awards."""

    strategies: List[AwardStrategy]

    def __init__(self):
        """Initialize with all award strategies."""
        self.strategies = [
            TierBasedAwardStrategy(),
            ActivityConsistencyAwardStrategy(),
            BalancedContributorAwardStrategy(),
            PRCharacteristicAwardStrategy(),
            RoleBasedAwardStrategy(),
            QualityAwardStrategy(),
            ThemeBasedAwardStrategy(),
        ]

    def determine_awards(self, collection: CollectionResult) -> List[str]:
        """Determine all awards by running all strategies.

        Args:
            collection: Collection of repository data

        Returns:
            List of award strings. If no awards are found, returns default award.
        """
        awards = []

        # Run all strategies
        for strategy in self.strategies:
            strategy_awards = strategy.calculate(collection)
            awards.extend(strategy_awards)

        # If no awards were given, use default
        if not awards:
            default_strategy = DefaultAwardStrategy()
            awards = default_strategy.calculate(collection)

        return awards
