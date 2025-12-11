"""Performance awareness checker for witch critique."""

from __future__ import annotations

from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from github_feedback.core.models import CollectionResult, WitchCritiqueItem

from github_feedback.core.models import WitchCritiqueItem


class PerformanceChecker:
    """Check for performance awareness in development practices."""

    @staticmethod
    def check_optimization_awareness(collection, critiques: List[WitchCritiqueItem]) -> None:
        """Check if developer shows awareness of performance optimization."""
        if not collection.pull_request_examples:
            return

        # Check for performance-related PRs
        perf_keywords = ['performance', 'optimize', '속도', '최적화', 'cache', 'lazy', 'memo']
        perf_prs = [pr for pr in collection.pull_request_examples
                    if any(kw in pr.title.lower() for kw in perf_keywords)]

        # If very few PRs mention performance
        if len(collection.pull_request_examples) > 15 and len(perf_prs) == 0:
            critiques.append(
                WitchCritiqueItem(
                    category="성능 인식",
                    severity="🕷️ 경고",
                    critique=f"{len(collection.pull_request_examples)}개 PR 중 성능 관련이 하나도 없네? '일단 돌아가게'만 만들고 성능은 안중에도 없어?",
                    evidence=f"{len(collection.pull_request_examples)}개 PR 중 성능 관련 0개",
                    consequence="느린 앱, 사용자 이탈, 서버 비용 증가, 나중에 대규모 리팩토링.",
                    remedy="프로파일링 습관화. Big O 고려. 캐싱 전략. DB 쿼리 최적화. 측정 후 최적화."
                )
            )

    @staticmethod
    def check_large_data_handling(collection, critiques: List[WitchCritiqueItem]) -> None:
        """Warn about potential inefficient data handling."""
        if not collection.pull_request_examples:
            return

        # Heuristic: Very large additions might indicate data duplication or inefficient handling
        very_large_additions = [pr for pr in collection.pull_request_examples
                                if pr.additions > 5000]

        if len(very_large_additions) > 2:
            critiques.append(
                WitchCritiqueItem(
                    category="데이터 처리",
                    severity="⚡ 심각",
                    critique=f"{len(very_large_additions)}개 PR이 각각 5000줄 이상 추가? 데이터를 복붙하거나 비효율적으로 처리하고 있는 건 아니야?",
                    evidence=f"{len(very_large_additions)}개 PR이 5000줄 이상 추가",
                    consequence="메모리 부족, 느린 로딩, 저장소 비대화, 머지 충돌 지옥.",
                    remedy="데이터 정규화. 외부 파일/DB 활용. Generator 사용. 페이지네이션. 중복 제거."
                )
            )

    @staticmethod
    def check_algorithm_complexity(collection, critiques: List[WitchCritiqueItem]) -> None:
        """Check awareness of algorithmic complexity."""
        if not collection.pull_request_examples:
            return

        # If many PRs touch the same files repeatedly (might indicate inefficient algorithms being patched)
        # This is a rough heuristic
        total_prs = len(collection.pull_request_examples)

        if total_prs > 20:
            # Random general advice for performance thinking
            critiques.append(
                WitchCritiqueItem(
                    category="알고리즘 복잡도",
                    severity="💫 조언",
                    critique="반복문 안에 반복문 돌리고, DB 쿼리 N번 날리고... 시간 복잡도 O(n²)이 뭔지 알아? '일단 돌아가니까' 끝?",
                    evidence=f"{total_prs}개 PR 분석 완료",
                    consequence="데이터 증가하면 시스템 마비. 사용자 급증 시 서버 다운. 스케일링 불가.",
                    remedy="시간/공간 복잡도 공부. 적절한 자료구조 선택. N+1 문제 인지. 알고리즘 최적화."
                )
            )
