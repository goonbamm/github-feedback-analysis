"""Code style and maintainability checker for witch critique."""

from __future__ import annotations

from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from github_feedback.core.models import CollectionResult, DetailedFeedbackSnapshot, WitchCritiqueItem

from github_feedback.core.models import WitchCritiqueItem


class CodeStyleChecker:
    """Check code style and maintainability issues."""

    @staticmethod
    def check_file_organization(collection, critiques: List[WitchCritiqueItem]) -> None:
        """Check for signs of poor file organization."""
        if not collection.pull_request_examples:
            return

        # Check if PRs tend to modify many files (sign of poor separation of concerns)
        avg_files_per_pr = sum(
            len(getattr(pr, 'files_changed', [])) if hasattr(pr, 'files_changed') else 0
            for pr in collection.pull_request_examples
        ) / len(collection.pull_request_examples) if collection.pull_request_examples else 0

        if avg_files_per_pr > 20:
            critiques.append(
                WitchCritiqueItem(
                    category="파일 구조",
                    severity="💀 위험",
                    critique=f"PR당 평균 {avg_files_per_pr:.0f}개 파일 수정? 파일 하나 고치려면 온 프로젝트를 건드려야 해? 분리가 안 돼 있네.",
                    evidence=f"평균 {avg_files_per_pr:.0f}개 파일/PR",
                    consequence="코드 이해 어려움, 테스트 복잡도 증가, 버그 연쇄 작용, 리팩토링 공포.",
                    remedy="관심사 분리(Separation of Concerns) 원칙 적용. 모듈화, 단일 책임 원칙 따르기."
                )
            )

    @staticmethod
    def check_naming_consistency(detailed_feedback, critiques: List[WitchCritiqueItem]) -> None:
        """Check for inconsistent naming in commits/PRs."""
        if not detailed_feedback or not detailed_feedback.commit_feedback:
            return

        commit_fb = detailed_feedback.commit_feedback

        # Check for inconsistent prefixes/styles in commit messages
        # This is a heuristic - if we see lots of different patterns, naming might be inconsistent
        if commit_fb.total_commits > 10:
            # If less than 30% of commits follow conventional format, flag it
            conventional_ratio = (commit_fb.total_commits - commit_fb.poor_messages) / commit_fb.total_commits

            if conventional_ratio < 0.5:
                critiques.append(
                    WitchCritiqueItem(
                        category="네이밍 일관성",
                        severity="🕷️ 경고",
                        critique="커밋 메시지 스타일이 중구난방이야. 'feat:', 'fix:', 'update', '수정'... 팀원마다 다른 스타일? 컨벤션 없어?",
                        evidence=f"{commit_fb.total_commits}개 커밋 중 {conventional_ratio*100:.0f}%만 일관된 형식",
                        consequence="히스토리 검색 어려움, 릴리스 노트 자동화 불가, 팀 혼선.",
                        remedy="Conventional Commits 채택. 팀 컨벤션 문서화. Pre-commit hook으로 강제."
                    )
                )

    @staticmethod
    def check_magic_numbers(collection, critiques: List[WitchCritiqueItem]) -> None:
        """Warn about potential code smells based on PR patterns."""
        if not collection.pull_request_examples:
            return

        # Heuristic: If many PRs have "fix" in title shortly after features,
        # might indicate rushed code with magic numbers/hardcoding
        fix_prs = [pr for pr in collection.pull_request_examples
                   if any(word in pr.title.lower() for word in ['fix', '수정', 'hotfix', 'bugfix'])]

        fix_ratio = len(fix_prs) / len(collection.pull_request_examples)

        if fix_ratio > 0.4:  # More than 40% are fixes
            critiques.append(
                WitchCritiqueItem(
                    category="코드 스멜",
                    severity="💀 위험",
                    critique=f"PR의 {fix_ratio*100:.0f}%가 버그 수정? 첫 시도에 제대로 안 짜는 게 습관이야? 매직 넘버, 하드코딩 남발하고 있지?",
                    evidence=f"{len(collection.pull_request_examples)}개 PR 중 {len(fix_prs)}개가 수정",
                    consequence="기술 부채 누적, 유지보수 지옥, 코드 신뢰도 추락, 끝없는 버그 픽스.",
                    remedy="상수 정의해. 설정 외부화. 테스트 작성해. 코드 리뷰 꼼꼼히. 급하게 짜지 마."
                )
            )
