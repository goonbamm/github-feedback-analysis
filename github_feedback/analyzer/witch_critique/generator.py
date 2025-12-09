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
    CodeStyleChecker,
    PerformanceChecker,
    ErrorHandlingChecker,
    SecurityChecker,
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

        # Run all checks - Original checkers
        CommitQualityChecker.check(detailed_feedback, critiques)
        PRQualityChecker.check_pr_size(collection, critiques)
        PRQualityChecker.check_pr_title(detailed_feedback, critiques)
        PRQualityChecker.check_pr_description(collection, critiques)
        PRQualityChecker.check_large_file_changes(collection, critiques)
        ReviewQualityChecker.check(collection, detailed_feedback, critiques)
        ReviewQualityChecker.check_review_depth(collection, critiques)
        ActivityChecker.check_consistency(collection, critiques)
        ActivityChecker.check_branch_management(collection, critiques)
        ActivityChecker.check_weekend_warrior(collection, critiques)
        DocumentationChecker.check(collection, critiques)
        DocumentationChecker.check_api_documentation(collection, critiques)
        TestingChecker.check(collection, critiques)
        CollaborationChecker.check_issue_tracking(collection, critiques)
        CollaborationChecker.check_diversity(collection, critiques)
        PatternChecker.check(collection, detailed_feedback, critiques)

        # Run new comprehensive checkers
        CodeStyleChecker.check_file_organization(collection, critiques)
        CodeStyleChecker.check_naming_consistency(detailed_feedback, critiques)
        CodeStyleChecker.check_magic_numbers(collection, critiques)
        PerformanceChecker.check_optimization_awareness(collection, critiques)
        PerformanceChecker.check_large_data_handling(collection, critiques)
        PerformanceChecker.check_algorithm_complexity(collection, critiques)
        ErrorHandlingChecker.check_error_handling_awareness(collection, critiques)
        ErrorHandlingChecker.check_defensive_programming(collection, critiques)
        ErrorHandlingChecker.check_logging_monitoring(collection, critiques)
        SecurityChecker.check_security_awareness(collection, critiques)
        SecurityChecker.check_dependency_updates(collection, critiques)
        SecurityChecker.check_secrets_management(collection, critiques)

        # If no specific critiques, add fallback so witch always appears
        # Now with more diverse and comprehensive critiques
        if not critiques:
            critiques.append(self._get_random_general_critique(collection))

        # Create witch critique with opening and closing
        opening_curses = [
            "🔮 자, 수정 구슬을 들여다보니... 흠, 개선할 게 좀 보이는군.",
            "🔮 크리스탈 볼이 말하길... 너한테 할 말이 좀 있대.",
            "🔮 예언의 수정 구슬에 미래가 보여. 이대로면 내년에도 똑같은 실수 반복할 텐데?",
            "🔮 수정 구슬 속에 네 코드가 보이는데... 음, 할 말이 많네.",
            "🔮 완벽한 사람은 없어. 너도 예외는 아니야. 들어볼래?",
            "🔮 개발자로서 잘하고 있긴 한데... 더 잘할 수 있어. 귀 좀 열어봐.",
        ]

        closing_prophecies = [
            "💫 이 독설들을 무시하면 내년에도 똑같은 얘기 들을 거야. 하지만 하나씩만 고쳐도 훨씬 나아질 거라는 것도 보여. 선택은 네 몫이야.",
            "💫 마녀의 조언은 여기까지. 듣든 말든 너 맘이지만, 1년 후 더 나은 개발자가 되고 싶다면... 뭐, 알아서 해.",
            "💫 수정 구슬이 보여주는 미래: 이것들만 고치면 내년엔 꽤 괜찮은 개발자가 될 수 있어. 안 고치면? 그건 네가 더 잘 알겠지.",
            "💫 독설은 여기까지. 상처받지 말고 성장의 기회로 삼길. 완벽한 개발자는 없으니까.",
            "💫 크리스탈 볼을 덮는다. 받아들이기 힘들겠지만, 진실은 성장의 시작이야. 파이팅.",
        ]

        return WitchCritique(
            opening_curse=random.choice(opening_curses),
            critiques=critiques,
            closing_prophecy=random.choice(closing_prophecies)
        )

    def _get_random_general_critique(self, collection: CollectionResult) -> WitchCritiqueItem:
        """Get a random general critique for developers with no specific issues.

        This includes general advice, excellence traps, and growth mindset critiques
        to ensure the witch always has something meaningful to say, even to
        seemingly perfect developers.

        Args:
            collection: Collection of repository data for evidence text

        Returns:
            A randomly selected general improvement critique
        """
        general_critiques = [
            # Original general critiques
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

            # NEW: Excellence traps and advanced topics
            WitchCritiqueItem(
                category="완벽주의 함정",
                severity="💫 조언",
                critique="코드가 완벽할 때까지 PR 안 올리고 혼자 고민하고 있지? 완벽주의는 오히려 성장을 막아.",
                evidence=f"총 {collection.commits}개 커밋 활동 분석",
                consequence="피드백 늦게 받아서 방향 틀리고, 팀 협업 타이밍 놓치고, 혼자만의 기준에 갇혀.",
                remedy="70% 완성되면 초안 공유. Early feedback이 완벽한 최종본보다 가치 있어. Iterate fast."
            ),
            WitchCritiqueItem(
                category="기술 스택 다양성",
                severity="💫 조언",
                critique="하나의 언어, 하나의 프레임워크만 파고 있지 않아? 다른 생태계 보면 시야가 넓어져.",
                evidence="기술 스택 패턴 검토",
                consequence="기술 편식하면 문제 해결 방법도 한정돼. '망치만 있으면 모든 게 못으로 보인다'는 말 알지?",
                remedy="다른 패러다임 언어 하나 배워봐. 함수형, 객체지향, 절차지향 다 경험해. 시야 넓혀."
            ),
            WitchCritiqueItem(
                category="멘토링 & 지식 전파",
                severity="💫 조언",
                critique="주니어 개발자 도와주거나, 블로그 쓰거나, 컨퍼런스 발표 해봤어? 가르치면서 더 배우게 돼.",
                evidence=f"{collection.pull_requests}개 PR, {collection.reviews}개 리뷰 분석",
                consequence="지식 독점하면 개인은 성장해도 팀은 안 성장해. 결국 너만 바빠지고 병목 됨.",
                remedy="주니어 멘토링. 블로그 시작. 스터디 리드. 가르치는 게 최고의 학습이야."
            ),
            WitchCritiqueItem(
                category="사용자 중심 사고",
                severity="💫 조언",
                critique="기술적으로 멋진 코드 짜는 데만 집중하고, 실제 사용자 니즈는 고민 안 하지?",
                evidence="개발 활동 전반 검토",
                consequence="아무도 안 쓰는 기능 만들고, 사용자 불편함 모르고, 비즈니스 임팩트 없고, 개발자 자기만족.",
                remedy="사용자 피드백 들어. Analytics 봐. A/B 테스트 해. 개발자는 문제 해결자야, 코드 장인 이전에."
            ),
            WitchCritiqueItem(
                category="아키텍처 설계",
                severity="💫 조언",
                critique="당장 돌아가게만 짜고, 확장성이나 유지보수성은 나중 문제라고 생각하지 않아?",
                evidence=f"{collection.commits}개 커밋 구조 분석",
                consequence="프로젝트 커지면 스파게티 코드, 리팩토링 불가, 신기능 추가마다 악몽, 결국 재작성.",
                remedy="SOLID 원칙. 디자인 패턴. 확장성 고려. 당장은 오버엔지니어링처럼 보여도 나중에 감사하게 돼."
            ),
            WitchCritiqueItem(
                category="데이터 중심 의사결정",
                severity="💫 조언",
                critique="'이게 더 나을 것 같은데'로 결정하지 말고, 데이터로 증명해. 감이 아니라 숫자로 말해.",
                evidence="전체 개발 패턴 검토",
                consequence="주관적 판단 실패, 잘못된 우선순위, 시간 낭비, 팀 설득 실패, 리소스 오배치.",
                remedy="A/B 테스트. 메트릭 설정. 가설 검증. '이게 좋을 것 같아' < '데이터가 이렇게 나왔어'"
            ),
            WitchCritiqueItem(
                category="비즈니스 이해",
                severity="💫 조언",
                critique="회사가 어떻게 돈 버는지, 내 코드가 비즈니스에 어떤 영향 주는지 생각해 본 적 있어?",
                evidence="커밋 및 PR 활동 분석",
                consequence="기술만 아는 개발자는 Junior에 머물러. Senior는 비즈니스 임팩트를 이해하고 만들어.",
                remedy="프로덕트 미팅 참석. 비즈니스 지표 공부. '왜 이 기능 만드는지' 항상 물어봐."
            ),
            WitchCritiqueItem(
                category="실패에서 배우기",
                severity="💫 조언",
                critique="실수하면 감추려고만 하지 않아? 실패를 공유하고 배우는 게 팀 성장의 핵심이야.",
                evidence="개발 활동 패턴 분석",
                consequence="같은 실수 반복, 팀 전체가 비슷한 구덩이 빠짐, 심리적 안전감 없음, 혁신 없음.",
                remedy="포스트모템 문화. 블레임 없는 리뷰. '이번에 배운 것' 공유. 실패는 데이터야, 수치 아니고."
            ),
            WitchCritiqueItem(
                category="도구 자동화",
                severity="💫 조언",
                critique="반복 작업 수작업으로 하고 있지? 3번 이상 반복하면 자동화해. 시간이 곧 돈이야.",
                evidence=f"{collection.commits}개 커밋 활동 검토",
                consequence="반복 작업에 시간 낭비, 휴먼 에러, 생산성 하락, 진짜 중요한 일 못 함.",
                remedy="스크립트 작성. CI/CD 파이프라인. Pre-commit hook. Makefile. 10분 절약이 일주일이면 몇 시간?"
            ),
            WitchCritiqueItem(
                category="코드 소유권",
                severity="💫 조언",
                critique="'내가 짠 코드니까 내가 관리'? 코드 소유권은 팀 전체야. 버스에 치이면 어쩔 건데?",
                evidence=f"PR {collection.pull_requests}개, 협업 패턴 분석",
                consequence="Bus factor 1, 휴가도 못 가, 지식 사일로, 팀 확장 불가, 결국 너만 고생.",
                remedy="코드 리뷰 적극 참여. 페어 프로그래밍. 문서화. 지식 공유 세션. 팀이 함께 성장해야 해."
            ),
            WitchCritiqueItem(
                category="인프라 이해",
                severity="💫 조언",
                critique="'인프라는 데브옵스 팀이 알아서 하겠지'? 배포 환경 이해 없으면 반쪽짜리 개발자야.",
                evidence="전체 개발 활동 분석",
                consequence="프로덕션 이슈 대응 못 함, 성능 문제 원인 파악 못 함, 배포 실패 시 멘붕.",
                remedy="Docker 공부. CI/CD 이해. 로그 보는 법. 모니터링 도구. 배포부터 운영까지가 개발이야."
            ),
            WitchCritiqueItem(
                category="기술 트렌드",
                severity="💫 조언",
                critique="최신 기술 트렌드 쫓기만 하고, 왜 나왔는지 본질은 이해 안 하지 않아?",
                evidence="기술 스택 활용 패턴",
                consequence="유행 쫓다 핵심 놓침, 불필요한 복잡도, 검증 안 된 기술 도입, 나중에 후회.",
                remedy="왜(Why) 먼저 이해. 문제 정의하고 기술 선택. '쿨하니까' < '이 문제 해결에 최적이니까'"
            ),
            WitchCritiqueItem(
                category="코드 리뷰 문화",
                severity="💫 조언",
                critique="리뷰 받으면 방어적으로 나오거나, 리뷰할 때 비난조로 쓰지 않아? 리뷰는 성장의 기회야.",
                evidence=f"{collection.reviews}개 리뷰 활동 분석",
                consequence="팀 분위기 나빠지고, 리뷰 회피하고, 코드 품질 떨어지고, 성장 기회 놓침.",
                remedy="Constructive한 피드백. '이렇게 하면 어때요?' > '이거 잘못됐어요'. 배우는 자세."
            ),
            WitchCritiqueItem(
                category="레거시 코드 다루기",
                severity="💫 조언",
                critique="레거시 코드 보면 욕만 하고 회피하지? 레거시 개선이 진짜 실력이야.",
                evidence=f"{collection.commits}개 커밋 패턴 검토",
                consequence="레거시 방치, 기술 부채 누적, 신규 기능 추가 어려움, 팀 생산성 하락.",
                remedy="점진적 리팩토링. Strangler Fig 패턴. 테스트 먼저 추가. 레거시 정복이 시니어의 길."
            ),
            WitchCritiqueItem(
                category="개발 속도 vs 품질",
                severity="💫 조언",
                critique="빠르게 개발하는 것과 제대로 개발하는 것, 둘 다 중요해. 편향되면 나중에 더 느려져.",
                evidence=f"총 {collection.commits}개 커밋, {collection.pull_requests}개 PR 분석",
                consequence="빠르기만 하면 버그 폭탄, 품질만 추구하면 데드라인 놓침, 둘 다 실패.",
                remedy="MVP 개념. 핵심만 빠르게, 점진적 개선. Technical debt 의식하며 속도 조절. 균형이 답."
            ),
            WitchCritiqueItem(
                category="네트워킹",
                severity="💫 조언",
                critique="개발자 커뮤니티 활동 안 하지? 컨퍼런스, 밋업, 오픈소스... 네트워크도 실력이야.",
                evidence="전체 활동 패턴 분석",
                consequence="정보 고립, 트렌드 놓침, 좋은 기회 못 잡음, 커리어 성장 더딤.",
                remedy="컨퍼런스 참석. 오픈소스 기여. 기술 블로그. 밋업 참여. 사람이 곧 기회야."
            ),
            WitchCritiqueItem(
                category="기술 외 역량",
                severity="💫 조언",
                critique="코딩 실력만 키우면 다야? 프레젠테이션, 협상, 기획... Soft skill도 중요해.",
                evidence="협업 및 커뮤니케이션 패턴 검토",
                consequence="아이디어 있어도 설득 못 함, 프로젝트 리드 못 함, 시니어 승진 막힘.",
                remedy="발표 연습. 문서 작성. 회의 주도. 경청 능력. 기술력 + 소프트스킬 = 진짜 시니어."
            ),
            WitchCritiqueItem(
                category="건강과 지속가능성",
                severity="💫 조언",
                critique="밤새 코딩, 주말 출근, 운동 안 함... 단기 스프린트는 되지만 마라톤은 못 뛰어.",
                evidence=f"{collection.commits}개 커밋 활동 시간 패턴",
                consequence="번아웃, 건강 악화, 장기적 생산성 폭락, 경력 중단, 삶의 질 하락.",
                remedy="규칙적인 운동. 충분한 수면. 취미 생활. 일과 삶의 균형. 10년 뛸 체력 만들어."
            ),
            WitchCritiqueItem(
                category="Imposter Syndrome",
                severity="💫 조언",
                critique="'나는 아직 멀었어' 하면서 자신감 없지? 가면 증후군에 빠지지 마. 너도 잘하고 있어.",
                evidence=f"총 {collection.commits}개 커밋 성과 분석",
                consequence="자신감 부족, 기회 거절, 도전 회피, 성장 정체, 실력은 있는데 발휘 못 함.",
                remedy="성취 기록해. 피드백 받아들여. 완벽하지 않아도 괜찮아. 성장 과정 인정해."
            ),
            WitchCritiqueItem(
                category="기술 선택 기준",
                severity="💫 조언",
                critique="기술 선택할 때 '이력서에 좋아 보여서'로 결정하지 말고, 프로젝트에 맞는지 봐.",
                evidence="기술 스택 사용 패턴",
                consequence="오버엔지니어링, 팀 학습 부담, 유지보수 지옥, 프로젝트 실패.",
                remedy="문제 먼저, 기술은 그다음. Boring Technology 선택도 현명한 결정. 검증된 것의 가치."
            ),
        ]

        return random.choice(general_critiques)
