#!/usr/bin/env python3
"""Demo script to showcase the Witch's Critique feature."""

from datetime import datetime
from pathlib import Path

from github_feedback.models import (
    AnalysisFilters,
    AnalysisStatus,
    CollectionResult,
    MetricSnapshot,
    WitchCritique,
    WitchCritiqueItem,
)
from github_feedback.reporter import Reporter


def create_demo_metrics() -> MetricSnapshot:
    """Create a demo MetricSnapshot with witch's critique."""

    # Create collection result
    collection = CollectionResult(
        repo="goonbamm/github-feedback-analysis",
        months=12,
        collected_at=datetime.now(),
        commits=150,
        pull_requests=35,
        reviews=20,
        issues=10,
        filters=AnalysisFilters(),
    )

    # Create witch's critique with multiple severity levels
    witch_critique = WitchCritique(
        opening_curse="🔮 자, 수정 구슬을 들여다보니... 흠, 개선할 게 좀 보이는군.",
        critiques=[
            WitchCritiqueItem(
                category="커밋 메시지",
                severity="🔥 치명적",
                critique="커밋 메시지의 45%가 형편없어. '수정', 'fix', 'update' 같은 게 전부야? 6개월 후 너 자신도 뭘 고쳤는지 모를 텐데.",
                evidence="150개 커밋 중 68개가 불량",
                consequence="나중에 버그 찾느라 git log 보면서 시간 낭비할 거야. 팀원들도 네 변경사항 이해 못 해.",
                remedy="커밋 메시지에 '왜'를 담아. 'fix: 로그인 시 토큰 만료 체크 누락 수정' 이런 식으로."
            ),
            WitchCritiqueItem(
                category="PR 크기",
                severity="⚡ 심각",
                critique="PR 하나에 평균 850줄? 리뷰어들 괴롭히는 게 취미야? 큰 PR은 안 읽힌다는 거 몰라?",
                evidence="12개 PR이 1000줄 이상",
                consequence="리뷰 품질 떨어지고, 버그 놓치고, 머지 충돌 지옥에 빠질 거야.",
                remedy="PR은 300줄 이하로. 큰 기능은 쪼개서 여러 PR로 나눠. Feature flag 써."
            ),
            WitchCritiqueItem(
                category="코드 리뷰",
                severity="🕷️ 경고",
                critique="리뷰의 65%가 그냥 'LGTM' 수준이야. 진짜 코드 읽긴 한 거야?",
                evidence="20개 리뷰 중 13개가 형식적",
                consequence="팀 코드 품질 떨어지고, 버그 프로덕션에서 발견되고.",
                remedy="구체적인 피드백 줘. '이 함수 복잡도 높은데 테스트 추가하면 어때?' 이런 식으로."
            ),
        ],
        closing_prophecy="💫 이 독설들을 무시하면 내년에도 똑같은 얘기 들을 거야. 하지만 하나씩만 고쳐도 훨씬 나아질 거라는 것도 보여. 선택은 네 몫이야."
    )

    # Create minimal metrics snapshot
    metrics = MetricSnapshot(
        repo="goonbamm/github-feedback-analysis",
        months=12,
        generated_at=datetime.now(),
        status=AnalysisStatus.REPORTED,
        summary={"overview": "Demo metrics to showcase witch's critique"},
        stats={},
        evidence={},
        witch_critique=witch_critique,
    )

    return metrics


def main():
    """Generate a demo report showcasing the witch's critique feature."""
    print("🔮 마녀의 독설 기능 데모를 생성합니다...\n")

    # Create demo metrics
    metrics = create_demo_metrics()

    # Create reporter
    reporter = Reporter(output_dir=Path("demo_reports"))

    # Generate markdown content (in-memory)
    content = reporter.generate_markdown_content(metrics)

    # Find the witch's critique section
    lines = content.split('\n')
    witch_section = []
    in_witch_section = False

    for line in lines:
        if '## 🔮 마녀의 독설' in line:
            in_witch_section = True
        elif line.startswith('## ') and in_witch_section:
            break

        if in_witch_section:
            witch_section.append(line)

    # Save to file
    output_file = Path("demo_reports/witch_critique_demo.md")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text('\n'.join(witch_section), encoding='utf-8')

    print(f"✅ 데모 보고서 생성 완료: {output_file}")
    print(f"\n📊 마녀의 독설 섹션 미리보기:\n")
    print("=" * 80)
    print('\n'.join(witch_section[:50]))  # Print first 50 lines
    print("=" * 80)
    print(f"\n💡 전체 내용은 {output_file} 파일을 확인하세요!")


if __name__ == "__main__":
    main()
