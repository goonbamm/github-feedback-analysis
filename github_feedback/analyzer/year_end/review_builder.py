"""Year-end review builder for annual retrospectives."""

from __future__ import annotations

from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from github_feedback.core.models import CollectionResult, PullRequest

from github_feedback.core.constants import ACTIVITY_THRESHOLDS, DISPLAY_LIMITS
from github_feedback.core.models import YearEndReview
from github_feedback.analyzer.helpers import ActivityMessageBuilder, InsightExtractor


class YearEndReviewBuilder:
    """Build year-end review content."""

    @staticmethod
    def _calculate_pr_size(pr: PullRequest) -> int:
        """Calculate the total size of a pull request (additions + deletions)."""
        return pr.additions + pr.deletions

    @staticmethod
    def _get_total_changes(prs: List[PullRequest]) -> int:
        """Calculate total changes across all pull requests."""
        return sum(YearEndReviewBuilder._calculate_pr_size(pr) for pr in prs)

    @staticmethod
    def _find_largest_pr(prs: List[PullRequest]) -> PullRequest:
        """Find the pull request with the most changes."""
        return max(prs, key=YearEndReviewBuilder._calculate_pr_size)

    @staticmethod
    def _extract_proudest_moments(collection: CollectionResult) -> List[str]:
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
            total_changes = YearEndReviewBuilder._get_total_changes(collection.pull_request_examples)
            msg = ActivityMessageBuilder.build_if_exceeds(
                total_changes,
                ACTIVITY_THRESHOLDS['very_large_pr'],
                "총 {:,}줄의 코드 변경으로 대규모 개선을 주도했습니다.",
                total_changes
            )
            if msg:
                moments.append(msg)

            # Find largest PR
            largest_pr = YearEndReviewBuilder._find_largest_pr(collection.pull_request_examples)
            largest_pr_size = YearEndReviewBuilder._calculate_pr_size(largest_pr)
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

    @staticmethod
    def _extract_biggest_challenges(collection: CollectionResult) -> List[str]:
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

    @staticmethod
    def _extract_lessons_learned(collection: CollectionResult) -> List[str]:
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

    @staticmethod
    def _extract_next_year_goals(collection: CollectionResult) -> List[str]:
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

    @staticmethod
    def build(collection: CollectionResult) -> YearEndReview:
        """Generate year-end specific review content based on actual data."""
        return YearEndReview(
            proudest_moments=YearEndReviewBuilder._extract_proudest_moments(collection),
            biggest_challenges=YearEndReviewBuilder._extract_biggest_challenges(collection),
            lessons_learned=YearEndReviewBuilder._extract_lessons_learned(collection),
            next_year_goals=YearEndReviewBuilder._extract_next_year_goals(collection),
        )
