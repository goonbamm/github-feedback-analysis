"""PR quality checker for witch critique."""

from __future__ import annotations

from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from github_feedback.models import CollectionResult, DetailedFeedbackSnapshot, WitchCritiqueItem

from github_feedback.constants import CRITIQUE_THRESHOLDS
from github_feedback.models import WitchCritiqueItem


class PRQualityChecker:
    """Check PR quality including size, title, description, and file changes."""

    @staticmethod
    def check_pr_size(collection, critiques: List[WitchCritiqueItem]) -> None:
        """Check PR size and add critique if too large."""
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

    @staticmethod
    def check_pr_title(detailed_feedback: Optional, critiques: List[WitchCritiqueItem]) -> None:
        """Check PR title quality and add critique if vague."""
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

    @staticmethod
    def check_pr_description(collection, critiques: List[WitchCritiqueItem]) -> None:
        """Check PR description quality and add critique if too brief or empty."""
        if not collection.pull_request_examples:
            return

        # Count PRs with empty or very short descriptions
        min_description_length = 20  # Minimum meaningful description length
        brief_prs = [pr for pr in collection.pull_request_examples
                     if len(getattr(pr, 'body', '') or '') < min_description_length]

        brief_ratio = len(brief_prs) / len(collection.pull_request_examples)
        if brief_ratio > CRITIQUE_THRESHOLDS.get('brief_pr_description_ratio', 0.3):
            critiques.append(
                WitchCritiqueItem(
                    category="PR 설명",
                    severity="💀 위험",
                    critique=f"PR의 {brief_ratio*100:.0f}%가 설명이 없거나 너무 짧아. '뭘 왜 바꿨는지'를 쓰라는 게 그렇게 어려워?",
                    evidence=f"{len(collection.pull_request_examples)}개 PR 중 {len(brief_prs)}개가 설명 부실",
                    consequence="리뷰어가 컨텍스트 파악하느라 시간 낭비, 리뷰 품질 하락, 나중에 히스토리 추적 불가.",
                    remedy="PR 설명에 최소한 (1)변경 이유 (2)구현 방법 (3)테스트 방법을 포함해. 템플릿 활용해."
                )
            )

    @staticmethod
    def check_large_file_changes(collection, critiques: List[WitchCritiqueItem]) -> None:
        """Check for PRs with excessively large single file changes."""
        if not collection.pull_request_examples:
            return

        # This is a heuristic: if a PR has very high additions/deletions
        # but low file count, it suggests large single file changes
        large_single_file_prs = []
        for pr in collection.pull_request_examples:
            total_changes = pr.additions + pr.deletions
            # If total changes > 1000 and we can infer likely single large file
            # (This is approximate - in real implementation would need file-level data)
            if total_changes > 1000:
                large_single_file_prs.append(pr)

        if len(large_single_file_prs) > len(collection.pull_request_examples) * 0.15:
            critiques.append(
                WitchCritiqueItem(
                    category="파일 크기",
                    severity="⚡ 심각",
                    critique=f"거대한 파일 변경이 {len(large_single_file_prs)}개나 발견됐어. 한 파일에 천 줄 넘게 고치는 게 정상이라고 생각해?",
                    evidence=f"{len(large_single_file_prs)}개 PR에서 대규모 단일 파일 변경 의심",
                    consequence="리뷰 불가능, 버그 숨기 쉬움, 머지 충돌 지옥, 코드 베이스 유지보수 악몽.",
                    remedy="큰 파일은 기능별로 분리해. 리팩토링은 단계별로 나눠서. 한 PR = 한 가지 목적."
                )
            )
