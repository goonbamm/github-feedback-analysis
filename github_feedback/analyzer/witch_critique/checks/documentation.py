"""Documentation culture checker for witch critique."""

from __future__ import annotations

from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from github_feedback.models import CollectionResult, WitchCritiqueItem

from github_feedback.constants import CRITIQUE_THRESHOLDS
from github_feedback.models import WitchCritiqueItem


class DocumentationChecker:
    """Check documentation practices."""

    @staticmethod
    def check(collection, critiques: List[WitchCritiqueItem]) -> None:
        """Check documentation practices and add critique if insufficient."""
        if not collection.pull_request_examples:
            return

        # Count documentation-related PRs
        doc_keywords = ['doc', 'readme', '문서', 'documentation', 'guide']
        doc_prs = [pr for pr in collection.pull_request_examples
                   if any(kw in pr.title.lower() for kw in doc_keywords)]

        doc_ratio = len(doc_prs) / len(collection.pull_request_examples)
        if doc_ratio < CRITIQUE_THRESHOLDS['min_doc_pr_ratio']:
            critiques.append(
                WitchCritiqueItem(
                    category="문서화",
                    severity="🕷️ 경고",
                    critique=f"문서 관련 PR이 전체의 {doc_ratio*100:.0f}%밖에 안 돼? 6개월 후 네 코드 이해 못 하는 건 너 자신이야.",
                    evidence=f"{len(collection.pull_request_examples)}개 PR 중 {len(doc_prs)}개만 문서 관련",
                    consequence="신규 팀원 온보딩 지옥, API 사용법 물어보는 슬랙 메시지 폭탄, 레거시 코드화 가속.",
                    remedy="README 업데이트, API 문서화, 아키텍처 다이어그램 추가. 코드만큼 문서도 중요해."
                )
            )
