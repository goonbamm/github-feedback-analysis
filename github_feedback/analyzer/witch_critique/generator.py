"""Witch critique generator - harsh but constructive feedback."""

from __future__ import annotations

import random
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from github_feedback.models import CollectionResult, DetailedFeedbackSnapshot

from github_feedback.models import WitchCritique, WitchCritiqueItem

from .checks import (
    ActivityChecker,
    CollaborationChecker,
    CommitQualityChecker,
    DocumentationChecker,
    PatternChecker,
    PRQualityChecker,
    ReviewQualityChecker,
    TestingChecker,
)


class WitchCritiqueGenerator:
    """Generate harsh but constructive critique from the witch."""

    def generate(
        self,
        collection: CollectionResult,
        detailed_feedback: Optional[DetailedFeedbackSnapshot] = None,
    ) -> WitchCritique:
        """Generate harsh but productive feedback.

        This method ALWAYS returns a WitchCritique object. Even when no specific
        issues are found, it provides general improvement suggestions to ensure
        the witch's critique is always present in the report.

        Args:
            collection: Collection of repository data
            detailed_feedback: Optional detailed feedback snapshot

        Returns:
            WitchCritique with harsh but productive feedback (always returns, never None)
        """
        critiques: List[WitchCritiqueItem] = []

        # Run all checks
        CommitQualityChecker.check(detailed_feedback, critiques)
        PRQualityChecker.check_pr_size(collection, critiques)
        PRQualityChecker.check_pr_title(detailed_feedback, critiques)
        PRQualityChecker.check_pr_description(collection, critiques)
        PRQualityChecker.check_large_file_changes(collection, critiques)
        ReviewQualityChecker.check(collection, detailed_feedback, critiques)
        ActivityChecker.check_consistency(collection, critiques)
        ActivityChecker.check_branch_management(collection, critiques)
        DocumentationChecker.check(collection, critiques)
        TestingChecker.check(collection, critiques)
        CollaborationChecker.check_issue_tracking(collection, critiques)
        CollaborationChecker.check_diversity(collection, critiques)
        PatternChecker.check(collection, detailed_feedback, critiques)

        # If no specific critiques, add fallback so witch always appears
        if not critiques:
            critiques.append(self._get_random_general_critique(collection))

        # Create witch critique with opening and closing
        opening_curses = [
            "🔮 자, 수정 구슬을 들여다보니... 흠, 개선할 게 좀 보이는군.",
            "🔮 크리스탈 볼이 말하길... 너한테 할 말이 좀 있대.",
            "🔮 예언의 수정 구슬에 미래가 보여. 이대로면 내년에도 똑같은 실수 반복할 텐데?",
        ]

        closing_prophecies = [
            "💫 이 독설들을 무시하면 내년에도 똑같은 얘기 들을 거야. 하지만 하나씩만 고쳐도 훨씬 나아질 거라는 것도 보여. 선택은 네 몫이야.",
            "💫 마녀의 조언은 여기까지. 듣든 말든 너 맘이지만, 1년 후 더 나은 개발자가 되고 싶다면... 뭐, 알아서 해.",
            "💫 수정 구슬이 보여주는 미래: 이것들만 고치면 내년엔 꽤 괜찮은 개발자가 될 수 있어. 안 고치면? 그건 네가 더 잘 알겠지.",
        ]

        return WitchCritique(
            opening_curse=random.choice(opening_curses),
            critiques=critiques,
            closing_prophecy=random.choice(closing_prophecies)
        )

    def _get_random_general_critique(self, collection: CollectionResult) -> WitchCritiqueItem:
        """Get a random general critique for developers with no specific issues.

        Args:
            collection: Collection of repository data for evidence text

        Returns:
            A randomly selected general improvement critique
        """
        general_critiques = [
            WitchCritiqueItem(
                category="개발자 성장",
                severity="💫 조언",
                critique="겉으로는 괜찮아 보이지만, 안주하면 퇴보하는 법이야. 지금이 딱 다음 레벨로 올라갈 때야.",
                evidence=f"총 {collection.commits}개 커밋, {collection.pull_requests}개 PR 분석 완료",
                consequence="현상 유지는 곧 뒤처지는 거야. 기술은 매일 발전하는데 너만 그 자리면?",
                remedy="새로운 기술 하나 배워봐. 오픈소스 기여하거나, 더 어려운 문제에 도전해봐."
            ),
            WitchCritiqueItem(
                category="코드 품질",
                severity="💫 조언",
                critique="코드는 일단 돌아가는데... 그냥 '돌아간다'로 만족할 거야? 아니면 '아름답게 돌아간다'를 목표로 할 거야?",
                evidence="커밋 히스토리 전체 분석 완료",
                consequence="동작하는 코드와 훌륭한 코드의 차이를 모르면, 영원히 시니어 개발자 못 돼.",
                remedy="리팩토링에 시간 투자해. 클린 코드 원칙 공부하고, 코드 리뷰에서 더 많이 배워."
            ),
            WitchCritiqueItem(
                category="협업 능력",
                severity="💫 조언",
                critique="혼자서는 잘하는데, 팀워크는 어때? 커뮤니케이션도 기술이야. 코딩만 잘한다고 다가 아니라고.",
                evidence=f"PR {collection.pull_requests}개, 리뷰 {collection.reviews}개 활동 확인",
                consequence="협업 못 하는 개발자는 혼자 할 수 있는 것만 할 수 있어. 큰 프로젝트는 무리.",
                remedy="PR 설명 더 자세히 써. 리뷰 댓글에 이유와 대안 제시해. 팀원들과 더 소통해."
            ),
            WitchCritiqueItem(
                category="학습 태도",
                severity="💫 조언",
                critique="익숙한 것만 반복하고 있지 않아? 편안함(comfort zone)에 머무르면 성장 없어.",
                evidence="활동 패턴 분석 완료",
                consequence="5년차인데 1년차 실력만 있는 개발자 되기 싫으면 변화 필요해.",
                remedy="매달 새로운 것 하나씩 시도해. 낯선 라이브러리, 다른 패러다임, 새로운 도구."
            ),
            WitchCritiqueItem(
                category="문서화",
                severity="💫 조언",
                critique="코드는 쓰는데 문서는? 6개월 후 네 코드 다시 볼 때 주석 없어서 후회하는 건 너야.",
                evidence="커밋 및 PR 패턴 분석",
                consequence="문서 없는 코드는 레거시가 되는 순간 아무도 못 건드려. 너도 못 건드리게 돼.",
                remedy="복잡한 로직에는 주석 달아. README 업데이트해. API는 문서화해."
            ),
            WitchCritiqueItem(
                category="테스트 문화",
                severity="💫 조언",
                critique="테스트 없이 코드 짜고 있는 건 아니겠지? '돌아가니까 됐지'는 초보 마인드야.",
                evidence="전체 개발 활동 검토",
                consequence="테스트 없는 리팩토링은 자살행위. 언젠가 배포하고 밤새 롤백하는 날 올 거야.",
                remedy="TDD는 아니어도, 핵심 로직은 테스트 작성해. Coverage 60% 이상 목표로."
            ),
            WitchCritiqueItem(
                category="코드 리뷰 참여",
                severity="💫 조언",
                critique="남의 코드 리뷰하는 시간도 네 실력 향상에 중요해. 혼자만 코딩하면 시야가 좁아져.",
                evidence=f"PR {collection.pull_requests}개, 리뷰 {collection.reviews}개 활동",
                consequence="다른 사람의 좋은 패턴 배울 기회를 놓치고, 팀에서 고립되고, 네 PR도 리뷰 못 받아.",
                remedy="매일 최소 2개 PR 리뷰해. 코멘트에 '왜 그렇게 생각하는지' 이유 포함해."
            ),
            WitchCritiqueItem(
                category="커뮤니케이션",
                severity="💫 조언",
                critique="코드만 잘 짜면 다야? PR 설명, 커밋 메시지도 커뮤니케이션이야. 글쓰기 실력도 개발자 역량이라고.",
                evidence="전체 활동 패턴 분석",
                consequence="의도 전달 실패, 리뷰어 시간 낭비, 프로젝트 히스토리 추적 불가, 협업 효율 감소.",
                remedy="PR 템플릿 만들어 써. 커밋 메시지에 맥락 담아. '왜'를 설명하는 습관 들여."
            ),
            WitchCritiqueItem(
                category="점진적 개선",
                severity="💫 조언",
                critique="완벽한 코드를 한 번에 짜려고 하지 마. 작게 시작해서 점진적으로 개선하는 게 프로야.",
                evidence=f"{collection.commits}개 커밋 패턴 분석",
                consequence="큰 변경은 리뷰 안 되고, 버그 많고, 롤백 어렵고, 팀 협업 방해돼.",
                remedy="작은 단위로 자주 커밋. 리팩토링은 단계별로. 'Make it work, make it right, make it fast' 순서 지켜."
            ),
            WitchCritiqueItem(
                category="기술 부채",
                severity="💫 조언",
                critique="'나중에 고치지 뭐'라고 생각하는 기술 부채들, 쌓이고 있지 않아? 나중은 절대 안 와.",
                evidence="코드 변경 패턴 검토",
                consequence="기술 부채는 복리로 쌓여. 나중엔 손댈 수도 없는 레거시 괴물이 돼.",
                remedy="매 스프린트 20%는 리팩토링에 투자. TODO 주석 남기지 말고 바로 이슈로 등록."
            ),
            WitchCritiqueItem(
                category="성능 최적화",
                severity="💫 조언",
                critique="성능 문제는 '나중에' 고치면 된다고? 아키텍처 잘못 잡으면 나중엔 손도 못 대.",
                evidence="전체 개발 활동 분석",
                consequence="사용자 이탈, 서버 비용 폭증, 나중에 전면 재작성, 시간 돈 날림.",
                remedy="병목 지점 프로파일링해. N+1 쿼리 잡아. 캐싱 전략 세워. 측정하지 않고 최적화하지 마."
            ),
            WitchCritiqueItem(
                category="보안 의식",
                severity="💫 조언",
                critique="보안은 '남 일'이 아니야. 네가 짠 코드 하나가 전체 시스템 해킹당하는 입구가 될 수 있어.",
                evidence="코드 리뷰 패턴 분석",
                consequence="데이터 유출, 법적 책임, 회사 신뢰 추락, 경력에 치명타.",
                remedy="입력값 검증 필수. SQL 인젝션, XSS 방어. 민감 정보 로그 남기지 마. 의존성 정기 업데이트."
            ),
        ]

        return random.choice(general_critiques)
