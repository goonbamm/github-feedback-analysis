"""Error handling and resilience checker for witch critique."""

from __future__ import annotations

from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from github_feedback.models import CollectionResult, WitchCritiqueItem

from github_feedback.models import WitchCritiqueItem


class ErrorHandlingChecker:
    """Check error handling and system resilience practices."""

    @staticmethod
    def check_error_handling_awareness(collection, critiques: List[WitchCritiqueItem]) -> None:
        """Check if developer shows error handling awareness."""
        if not collection.pull_request_examples:
            return

        # Check for error handling related PRs
        error_keywords = ['error', 'exception', 'try', 'catch', '에러', '예외', 'handling', 'validate']
        error_prs = [pr for pr in collection.pull_request_examples
                     if any(kw in pr.title.lower() for kw in error_keywords)]

        error_ratio = len(error_prs) / len(collection.pull_request_examples)

        # If very few PRs mention error handling (less than 5%)
        if len(collection.pull_request_examples) > 10 and error_ratio < 0.05:
            critiques.append(
                WitchCritiqueItem(
                    category="에러 처리",
                    severity="⚡ 심각",
                    critique=f"에러 처리 관련 PR이 {error_ratio*100:.1f}%? 'Happy path'만 코딩하고 예외 상황은 무시? 프로덕션에서 터지면 그때 봐?",
                    evidence=f"{len(collection.pull_request_examples)}개 PR 중 {len(error_prs)}개만 에러 처리 관련",
                    consequence="운영 장애, 데이터 손실, 사용자 불만, 새벽 긴급 호출, 로그 없어서 디버깅 지옥.",
                    remedy="모든 외부 호출에 에러 처리. 유효성 검증. 로깅. 모니터링. Graceful degradation."
                )
            )

    @staticmethod
    def check_defensive_programming(collection, critiques: List[WitchCritiqueItem]) -> None:
        """Warn about lack of defensive programming."""
        if not collection.pull_request_examples:
            return

        # Heuristic: If there are many small fix PRs, might indicate lack of defensive programming
        small_fix_prs = [pr for pr in collection.pull_request_examples
                        if (pr.additions + pr.deletions < 50) and
                        any(word in pr.title.lower() for word in ['fix', 'hotfix', 'patch', '긴급', '수정'])]

        if len(small_fix_prs) > len(collection.pull_request_examples) * 0.25:
            critiques.append(
                WitchCritiqueItem(
                    category="방어적 프로그래밍",
                    severity="💀 위험",
                    critique=f"작은 긴급 수정이 {len(small_fix_prs)}개? Null 체크 안 하지? Input validation 안 하지? 'undefined is not a function' 자주 보지?",
                    evidence=f"{len(small_fix_prs)}개의 소규모 긴급 수정 PR",
                    consequence="프로덕션 크래시, 데이터 오염, 보안 취약점, 신뢰도 하락.",
                    remedy="Null 체크 철저히. Type 검증. 경계 조건 테스트. Fail-fast 원칙. 에러 바운더리."
                )
            )

    @staticmethod
    def check_logging_monitoring(collection, critiques: List[WitchCritiqueItem]) -> None:
        """Check for logging and monitoring awareness."""
        if not collection.pull_request_examples:
            return

        # Check for logging/monitoring related PRs
        log_keywords = ['log', 'logging', 'monitor', 'metric', 'trace', '로깅', '모니터링', 'observability']
        log_prs = [pr for pr in collection.pull_request_examples
                   if any(kw in pr.title.lower() for kw in log_keywords)]

        # If no logging/monitoring PRs among many PRs
        if len(collection.pull_request_examples) > 15 and len(log_prs) == 0:
            critiques.append(
                WitchCritiqueItem(
                    category="로깅 & 모니터링",
                    severity="🕷️ 경고",
                    critique="로깅이나 모니터링 관련 PR이 하나도 없네? 프로덕션에서 뭔 일 일어나는지 모르는 채로 운영해? 장애 나면 어떻게 디버깅할 건데?",
                    evidence=f"{len(collection.pull_request_examples)}개 PR 중 로깅/모니터링 관련 0개",
                    consequence="장애 원인 파악 불가, 디버깅 시간 폭증, 재발 방지 불가, 사용자 경험 악화.",
                    remedy="구조화된 로깅. 메트릭 수집. 에러 트래킹(Sentry 등). APM 도입. 알람 설정."
                )
            )
