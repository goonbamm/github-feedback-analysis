"""Repetitive pattern checker for witch critique."""

from __future__ import annotations

from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from github_feedback.models import CollectionResult, DetailedFeedbackSnapshot, WitchCritiqueItem

from github_feedback.models import WitchCritiqueItem


class PatternChecker:
    """Check for repetitive problematic patterns."""

    @staticmethod
    def check(
        collection,
        detailed_feedback: Optional,
        critiques: List[WitchCritiqueItem]
    ) -> None:
        """Check for repetitive problematic patterns across commits and PRs."""
        # Check if multiple issues are consistently present
        issues_found = []

        # Check commit message issues
        if detailed_feedback and detailed_feedback.commit_feedback:
            commit_fb = detailed_feedback.commit_feedback
            if commit_fb.total_commits > 0:
                poor_ratio = commit_fb.poor_messages / commit_fb.total_commits
                if poor_ratio > 0.15:
                    issues_found.append("커밋 메시지")

        # Check PR title issues
        if detailed_feedback and detailed_feedback.pr_title_feedback:
            pr_fb = detailed_feedback.pr_title_feedback
            if pr_fb.total_prs > 0:
                vague_ratio = pr_fb.vague_titles / pr_fb.total_prs
                if vague_ratio > 0.15:
                    issues_found.append("PR 제목")

        # Check review tone issues
        if detailed_feedback and detailed_feedback.review_tone_feedback:
            review_fb = detailed_feedback.review_tone_feedback
            if review_fb.total_reviews > 0:
                harsh_ratio = review_fb.harsh_reviews / review_fb.total_reviews
                if harsh_ratio > 0.2:
                    issues_found.append("리뷰 톤")

        # If multiple patterns detected, add a meta-critique
        if len(issues_found) >= 3:
            critiques.append(
                WitchCritiqueItem(
                    category="반복 패턴",
                    severity="🔥 치명적",
                    critique=f"{', '.join(issues_found)} 등 여러 영역에서 같은 실수를 반복하고 있어. 배우는 게 없는 거야?",
                    evidence=f"{len(issues_found)}가지 문제 패턴이 지속적으로 관찰됨",
                    consequence="성장 정체, 팀의 신뢰 상실, 시니어 개발자로의 진급 불가, 똑같은 실수 무한 반복.",
                    remedy="패턴을 깨. 체크리스트 만들어서 PR 올리기 전에 확인해. 과거 피드백 다시 읽어봐."
                )
            )
