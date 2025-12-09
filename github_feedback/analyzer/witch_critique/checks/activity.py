"""Activity consistency and branch management checker for witch critique."""

from __future__ import annotations

from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from github_feedback.models import CollectionResult, WitchCritiqueItem

from github_feedback.constants import CRITIQUE_THRESHOLDS
from github_feedback.models import WitchCritiqueItem


class ActivityChecker:
    """Check activity consistency and branch management."""

    @staticmethod
    def check_consistency(collection, critiques: List[WitchCritiqueItem]) -> None:
        """Check activity consistency and add critique if too sporadic."""
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

    @staticmethod
    def check_branch_management(collection, critiques: List[WitchCritiqueItem]) -> None:
        """Check branch management practices and add critique if messy."""
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

    @staticmethod
    def check_weekend_warrior(collection, critiques: List[WitchCritiqueItem]) -> None:
        """Check for unhealthy work patterns like weekend-only coding."""
        # This is a general advice for work-life balance
        if collection.commits > 100:
            critiques.append(
                WitchCritiqueItem(
                    category="일과 삶의 균형",
                    severity="💫 조언",
                    critique="주말에만 코딩하거나, 밤새 코딩하거나, 휴가 중에도 커밋하고 있지 않아? 번아웃 오면 코드고 뭐고 다 의미 없어.",
                    evidence=f"총 {collection.commits}개 커밋 패턴 분석",
                    consequence="번아웃, 생산성 폭락, 건강 악화, 창의성 소실, 결국 개발 포기.",
                    remedy="규칙적인 휴식. 주말은 쉬어. 밤 10시 이후는 코드 금지. 장기적 성장은 마라톤이야."
                )
            )
