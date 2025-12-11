"""Commit message quality checker for witch critique."""

from __future__ import annotations

from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from github_feedback.core.models import DetailedFeedbackSnapshot, WitchCritiqueItem

from github_feedback.core.constants import CRITIQUE_THRESHOLDS
from github_feedback.core.models import WitchCritiqueItem


class CommitQualityChecker:
    """Check commit message quality."""

    @staticmethod
    def check(
        detailed_feedback: Optional[DetailedFeedbackSnapshot],
        critiques: List[WitchCritiqueItem]
    ) -> None:
        """Check commit message quality and add critique if poor.

        Args:
            detailed_feedback: Optional detailed feedback snapshot
            critiques: List to append critique to if issues found
        """
        if not detailed_feedback or not detailed_feedback.commit_feedback:
            return

        commit_fb = detailed_feedback.commit_feedback
        if commit_fb.total_commits == 0:
            return

        poor_ratio = commit_fb.poor_messages / commit_fb.total_commits
        if poor_ratio > CRITIQUE_THRESHOLDS['poor_commit_ratio']:
            critiques.append(
                WitchCritiqueItem(
                    category="커밋 메시지",
                    severity="🔥 치명적",
                    critique=f"커밋 메시지의 {poor_ratio*100:.0f}%가 형편없어. '수정', 'fix', 'update' 같은 게 전부야? 6개월 후 너 자신도 뭘 고쳤는지 모를 텐데.",
                    evidence=f"{commit_fb.total_commits}개 커밋 중 {commit_fb.poor_messages}개가 불량",
                    consequence="나중에 버그 찾느라 git log 보면서 시간 낭비할 거야. 팀원들도 네 변경사항 이해 못 해.",
                    remedy="커밋 메시지에 '왜'를 담아. 'fix: 로그인 시 토큰 만료 체크 누락 수정' 이런 식으로."
                )
            )
