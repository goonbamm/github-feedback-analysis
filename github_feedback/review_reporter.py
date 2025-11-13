"""Aggregate pull request reviews into an integrated annual report."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List

from .console import Console
from .llm import LLMClient
from .models import (
    GrowthIndicator,
    ImprovementArea,
    PersonalDevelopmentAnalysis,
    ReviewPoint,
    StrengthPoint,
)

console = Console()


@dataclass(slots=True)
class StoredReview:
    """Stored review summary reconstructed from cached artefacts."""

    number: int
    title: str
    author: str
    html_url: str
    created_at: datetime
    overview: str
    strengths: List[ReviewPoint]
    improvements: List[ReviewPoint]


class ReviewReporter:
    """Build integrated Korean reports from individual pull request reviews."""

    def __init__(self, *, output_dir: Path = Path("reports/reviews"), llm: LLMClient | None = None) -> None:
        self.output_dir = output_dir
        self.llm = llm

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _repo_dir(self, repo: str) -> Path:
        safe_repo = repo.replace("/", "__")
        return self.output_dir / safe_repo

    @staticmethod
    def _load_points(raw_points: Iterable[dict]) -> List[ReviewPoint]:
        points: List[ReviewPoint] = []
        for payload in raw_points:
            if not isinstance(payload, dict):
                continue
            message = str(payload.get("message") or "").strip()
            if not message:
                continue
            example_raw = payload.get("example")
            example = str(example_raw).strip() if example_raw else None
            points.append(ReviewPoint(message=message, example=example))
        return points

    def _load_reviews(self, repo: str) -> List[StoredReview]:
        repo_dir = self._repo_dir(repo)
        if not repo_dir.exists():
            return []

        reviews: List[StoredReview] = []
        for pr_dir in sorted(repo_dir.glob("pr-*")):
            summary_path = pr_dir / "review_summary.json"
            artefact_path = pr_dir / "artefacts.json"
            if not summary_path.exists() or not artefact_path.exists():
                continue

            try:
                summary_data = json.loads(summary_path.read_text(encoding="utf-8"))
                artefact_data = json.loads(artefact_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                console.log("Skipping invalid review artefact", str(pr_dir))
                continue

            try:
                number = int(artefact_data.get("number"))
                title = str(artefact_data.get("title") or "").strip()
                author = str(artefact_data.get("author") or "unknown").strip()
                html_url = str(artefact_data.get("html_url") or "").strip()
                created_at_raw = artefact_data.get("created_at")
                created_at = (
                    datetime.fromisoformat(created_at_raw)
                    if isinstance(created_at_raw, str)
                    else datetime.now(timezone.utc)
                )
            except Exception:  # pragma: no cover - defensive parsing guard
                console.log("Skipping malformed artefact", str(pr_dir))
                continue

            overview = str(summary_data.get("overview") or "").strip()
            strengths = self._load_points(summary_data.get("strengths", []))
            improvements = self._load_points(summary_data.get("improvements", []))

            reviews.append(
                StoredReview(
                    number=number,
                    title=title,
                    author=author,
                    html_url=html_url,
                    created_at=created_at,
                    overview=overview,
                    strengths=strengths,
                    improvements=improvements,
                )
            )

        reviews.sort(key=lambda item: (item.created_at, item.number))
        return reviews

    def _build_prompt_context(self, repo: str, reviews: List[StoredReview]) -> str:
        lines: List[str] = []
        lines.append(f"Repository: {repo}")
        lines.append(f"총 리뷰 PR 수: {len(reviews)}")
        lines.append("")
        lines.append("Pull Request 요약:")
        for review in reviews:
            lines.append(
                f"- PR #{review.number} {review.title} (작성자: {review.author}, 생성일: {review.created_at.date()})"
            )
            if review.html_url:
                lines.append(f"  URL: {review.html_url}")
            if review.overview:
                lines.append(f"  Overview: {review.overview}")
            if review.strengths:
                lines.append("  Strengths:")
                for point in review.strengths:
                    lines.append(f"    • {point.message}")
                    if point.example:
                        lines.append(f"      예시: {point.example}")
            if review.improvements:
                lines.append("  Improvements:")
                for point in review.improvements:
                    lines.append(f"    • {point.message}")
                    if point.example:
                        lines.append(f"      예시: {point.example}")
            lines.append("")

        return "\n".join(lines).strip()

    def _analyze_personal_development(
        self, repo: str, reviews: List[StoredReview]
    ) -> PersonalDevelopmentAnalysis:
        """Analyze personal development based on PR reviews using LLM."""
        if not self.llm or not reviews:
            return self._fallback_personal_development(reviews)

        context = self._build_prompt_context(repo, reviews)

        # Split reviews into early and recent for growth analysis
        midpoint = len(reviews) // 2
        early_reviews = reviews[:midpoint] if midpoint > 0 else []
        recent_reviews = reviews[midpoint:] if midpoint > 0 else reviews

        messages = [
            {
                "role": "system",
                "content": (
                    "당신은 개발자의 코드 기여 패턴을 분석하는 전문가입니다.\n\n"
                    "제공된 PR 리뷰 데이터를 바탕으로 개인의 **코드 작성 스타일, 기술적 강점, 개선 영역**을 "
                    "구체적인 근거와 함께 분석하세요. 일반적인 '장점/단점' 나열이 아닌, "
                    "**실제 코드와 PR에서 관찰되는 패턴**에 집중하세요.\n\n"
                    "**분석 원칙:**\n"
                    "1. 모든 인사이트는 구체적인 PR 예시로 뒷받침\n"
                    "2. 코드 기여의 특징을 카테고리별로 분류 (아키텍처 설계, 테스트 작성, 리팩토링, 문제 해결 등)\n"
                    "3. 개선 영역은 실행 가능한 구체적 제안과 함께 제공\n"
                    "4. 시간에 따른 변화는 초기 PR과 최근 PR의 실제 차이로 설명\n"
                    "5. 건설적이고 데이터 중심의 톤 유지\n\n"
                    "**응답 형식 (JSON):**\n"
                    "{\n"
                    '  "strengths": [\n'
                    "    {\n"
                    '      "category": "기술적 강점 카테고리",\n'
                    '      "description": "관찰된 패턴과 그 의미",\n'
                    '      "evidence": ["PR #번호: 구체적 코드/리뷰 예시", ...],\n'
                    '      "impact": "high|medium|low"\n'
                    "    }\n"
                    "  ],\n"
                    '  "improvement_areas": [\n'
                    "    {\n"
                    '      "category": "개선 영역 카테고리",\n'
                    '      "description": "현재 패턴의 제한점",\n'
                    '      "evidence": ["PR #번호: 구체적 예시", ...],\n'
                    '      "suggestions": ["실행 가능한 개선 방법", ...],\n'
                    '      "priority": "critical|important|nice-to-have"\n'
                    "    }\n"
                    "  ],\n"
                    '  "growth_indicators": [\n'
                    "    {\n"
                    '      "aspect": "변화가 관찰된 영역",\n'
                    '      "description": "구체적인 변화 내용",\n'
                    '      "before_examples": ["초기 PR의 특징"],\n'
                    '      "after_examples": ["최근 PR의 특징"],\n'
                    '      "progress_summary": "변화의 방향과 의미"\n'
                    "    }\n"
                    "  ],\n"
                    '  "overall_assessment": "코드 기여 패턴 종합 평가 (2-3문장)",\n'
                    '  "key_achievements": ["기술적으로 의미있는 기여", ...],\n'
                    '  "next_focus_areas": ["기술 역량 향상을 위한 집중 영역", ...]\n'
                    "}\n\n"
                    "각 배열은 최소 1개, 최대 5개 항목을 포함하세요."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"다음 PR 리뷰 데이터를 분석하여 개인의 코드 기여 패턴과 기술적 특징을 분석해주세요:\n\n"
                    f"{context}\n\n"
                    f"초기 PR 수: {len(early_reviews)}개\n"
                    f"최근 PR 수: {len(recent_reviews)}개\n\n"
                    "특히 다음 관점에서 분석해주세요:\n"
                    "1. 코드 설계 및 구조화 능력\n"
                    "2. 문제 해결 접근 방식\n"
                    "3. 테스트 및 문서화 습관\n"
                    "4. 기술 스택 활용 및 확장"
                ),
            },
        ]

        try:
            import json as json_module

            content = self.llm.complete(messages, temperature=0.4)
            data = json_module.loads(content)

            # Parse strengths
            strengths = []
            for item in data.get("strengths", []):
                strengths.append(
                    StrengthPoint(
                        category=item.get("category", "기타"),
                        description=item.get("description", ""),
                        evidence=item.get("evidence", []),
                        impact=item.get("impact", "medium"),
                    )
                )

            # Parse improvement areas
            improvement_areas = []
            for item in data.get("improvement_areas", []):
                improvement_areas.append(
                    ImprovementArea(
                        category=item.get("category", "기타"),
                        description=item.get("description", ""),
                        evidence=item.get("evidence", []),
                        suggestions=item.get("suggestions", []),
                        priority=item.get("priority", "medium"),
                    )
                )

            # Parse growth indicators
            growth_indicators = []
            for item in data.get("growth_indicators", []):
                growth_indicators.append(
                    GrowthIndicator(
                        aspect=item.get("aspect", ""),
                        description=item.get("description", ""),
                        before_examples=item.get("before_examples", []),
                        after_examples=item.get("after_examples", []),
                        progress_summary=item.get("progress_summary", ""),
                    )
                )

            return PersonalDevelopmentAnalysis(
                strengths=strengths,
                improvement_areas=improvement_areas,
                growth_indicators=growth_indicators,
                overall_assessment=data.get("overall_assessment", ""),
                key_achievements=data.get("key_achievements", []),
                next_focus_areas=data.get("next_focus_areas", []),
            )
        except Exception as exc:  # pragma: no cover
            console.log("LLM 개인 발전 분석 실패", str(exc))
            return self._fallback_personal_development(reviews)

    def _fallback_personal_development(
        self, reviews: List[StoredReview]
    ) -> PersonalDevelopmentAnalysis:
        """Provide basic personal development analysis without LLM."""
        # Collect all strengths and improvements from reviews
        all_strengths: List[tuple[StoredReview, ReviewPoint]] = []
        all_improvements: List[tuple[StoredReview, ReviewPoint]] = []

        for review in reviews:
            all_strengths.extend((review, point) for point in review.strengths)
            all_improvements.extend((review, point) for point in review.improvements)

        # Create basic strength points
        strengths = []
        for review, point in all_strengths[:5]:
            strengths.append(
                StrengthPoint(
                    category="코드 품질",
                    description=point.message,
                    evidence=[f"PR #{review.number}: {point.example or review.title}"],
                    impact="medium",
                )
            )

        # Create basic improvement areas
        improvement_areas = []
        for review, point in all_improvements[:5]:
            improvement_areas.append(
                ImprovementArea(
                    category="개선 영역",
                    description=point.message,
                    evidence=[f"PR #{review.number}: {point.example or review.title}"],
                    suggestions=["코드 리뷰 피드백을 참고하여 개선"],
                    priority="medium",
                )
            )

        # Basic growth analysis
        growth_indicators = []
        if len(reviews) >= 2:
            growth_indicators.append(
                GrowthIndicator(
                    aspect="지속적인 기여",
                    description=f"총 {len(reviews)}개의 PR을 통해 꾸준히 기여하고 있습니다.",
                    before_examples=[f"PR #{reviews[0].number}: {reviews[0].title}"],
                    after_examples=[f"PR #{reviews[-1].number}: {reviews[-1].title}"],
                    progress_summary="지속적으로 PR을 작성하며 프로젝트에 기여하고 있습니다.",
                )
            )

        return PersonalDevelopmentAnalysis(
            strengths=strengths,
            improvement_areas=improvement_areas,
            growth_indicators=growth_indicators,
            overall_assessment=f"총 {len(reviews)}개의 PR을 통해 프로젝트에 기여하고 있습니다.",
            key_achievements=[f"{len(reviews)}개의 PR 작성 및 리뷰 완료"],
            next_focus_areas=["코드 품질 향상", "테스트 커버리지 개선"],
        )

    # ------------------------------------------------------------------
    # Reporting
    # ------------------------------------------------------------------

    def _render_personal_development(
        self, analysis: PersonalDevelopmentAnalysis, reviews: List[StoredReview]
    ) -> List[str]:
        """Render personal development analysis section."""
        lines: List[str] = []
        lines.append("## 👤 개인 성장 분석")
        lines.append("")

        if analysis.overall_assessment:
            lines.append("### 전반적 평가")
            lines.append("")
            lines.append(analysis.overall_assessment)
            lines.append("")
            lines.append("---")
            lines.append("")

        # Create PR number to review mapping for link lookup
        pr_map = {review.number: review for review in reviews}

        def extract_pr_number(evidence: str) -> int | None:
            """Extract PR number from evidence string like 'PR #123: description'"""
            import re
            match = re.search(r'PR #(\d+)', evidence)
            return int(match.group(1)) if match else None

        # Strengths section
        lines.append("### ✨ 장점 (구체적 근거)")
        lines.append("")
        if analysis.strengths:
            lines.append("| 장점 | 근거/내용 | 링크 |")
            lines.append("|------|-----------|------|")
            for strength in analysis.strengths:
                impact_emoji = {"high": "🔥", "medium": "⭐", "low": "💫"}.get(
                    strength.impact, "⭐"
                )
                category = f"**{strength.category}** {impact_emoji}"

                # Combine description and evidence
                content_parts = [strength.description]
                if strength.evidence:
                    content_parts.append("<br>**구체적 근거:**")
                    for evidence in strength.evidence:
                        content_parts.append(f"• {evidence}")
                content = "<br>".join(content_parts)

                # Extract links from evidence
                links = []
                if strength.evidence:
                    for evidence in strength.evidence:
                        pr_num = extract_pr_number(evidence)
                        if pr_num and pr_num in pr_map:
                            review = pr_map[pr_num]
                            if review.html_url:
                                links.append(f"[PR #{pr_num}]({review.html_url})")

                link_cell = "<br>".join(links) if links else "-"
                lines.append(f"| {category} | {content} | {link_cell} |")
            lines.append("")
        else:
            lines.append("분석된 장점이 없습니다.")
            lines.append("")

        lines.append("---")
        lines.append("")

        # Improvement areas section
        lines.append("### 💡 보완점 (실행 가능한 제안)")
        lines.append("")
        if analysis.improvement_areas:
            # Sort by priority
            priority_order = {"critical": 0, "important": 1, "nice-to-have": 2}
            sorted_improvements = sorted(
                analysis.improvement_areas,
                key=lambda x: priority_order.get(x.priority, 1),
            )

            lines.append("| 개선점 | 근거/내용 | 링크 |")
            lines.append("|--------|-----------|------|")
            for area in sorted_improvements:
                priority_emoji = {
                    "critical": "🚨",
                    "important": "⚠️",
                    "nice-to-have": "💭",
                }.get(area.priority, "⚠️")
                category = f"**{area.category}** {priority_emoji}"

                # Combine description, evidence, and suggestions
                content_parts = [area.description]
                if area.evidence:
                    content_parts.append("<br>**구체적 예시:**")
                    for evidence in area.evidence:
                        content_parts.append(f"• {evidence}")
                if area.suggestions:
                    content_parts.append("<br>**개선 제안:**")
                    for suggestion in area.suggestions:
                        content_parts.append(f"• {suggestion}")
                content = "<br>".join(content_parts)

                # Extract links from evidence
                links = []
                if area.evidence:
                    for evidence in area.evidence:
                        pr_num = extract_pr_number(evidence)
                        if pr_num and pr_num in pr_map:
                            review = pr_map[pr_num]
                            if review.html_url:
                                links.append(f"[PR #{pr_num}]({review.html_url})")

                link_cell = "<br>".join(links) if links else "-"
                lines.append(f"| {category} | {content} | {link_cell} |")
            lines.append("")
        else:
            lines.append("분석된 보완점이 없습니다.")
            lines.append("")

        lines.append("---")
        lines.append("")

        # Growth indicators section
        lines.append("### 🌱 성장한 점 (시간에 따른 변화)")
        lines.append("")
        if analysis.growth_indicators:
            for i, growth in enumerate(analysis.growth_indicators, 1):
                lines.append(f"{i}. **{growth.aspect}**")
                lines.append(f"   - {growth.description}")
                if growth.before_examples:
                    lines.append("   - **초기 단계:**")
                    for example in growth.before_examples:
                        lines.append(f"     - {example}")
                if growth.after_examples:
                    lines.append("   - **현재 단계:**")
                    for example in growth.after_examples:
                        lines.append(f"     - {example}")
                if growth.progress_summary:
                    lines.append(f"   - **성장 요약:** {growth.progress_summary}")
                lines.append("")
        else:
            lines.append("- 분석된 성장 지표가 없습니다.")
            lines.append("")

        lines.append("---")
        lines.append("")

        # Key achievements
        if analysis.key_achievements:
            lines.append("### 🏆 주요 성과")
            lines.append("")
            for achievement in analysis.key_achievements:
                lines.append(f"- {achievement}")
            lines.append("")
            lines.append("---")
            lines.append("")

        # Next focus areas
        if analysis.next_focus_areas:
            lines.append("### 🎯 다음 집중 영역")
            lines.append("")
            for area in analysis.next_focus_areas:
                lines.append(f"- {area}")
            lines.append("")
            lines.append("---")
            lines.append("")

        return lines

    def _fallback_report(self, repo: str, reviews: List[StoredReview]) -> str:
        lines: List[str] = []
        lines.append("# 🎯 통합 코드 리뷰 보고서")
        lines.append("")
        lines.append(f"**저장소**: {repo}")
        lines.append(f"**검토한 PR 수**: {len(reviews)}건")
        lines.append("")
        lines.append("---")
        lines.append("")

        # Table of contents
        lines.append("## 📑 목차")
        lines.append("")
        lines.append("1. **👤 개인 성장 분석** - 장점, 보완점, 성장한 점")
        lines.append("2. **✨ 장점** - 뛰어났던 점들")
        lines.append("3. **💡 보완점** - 개선할 수 있는 부분")
        lines.append("4. **🌱 올해 성장한 점** - 성장 여정")
        lines.append("5. **🎊 전체 총평** - 종합 평가")
        lines.append("6. **📝 개별 PR 하이라이트** - 주요 PR 목록")
        lines.append("")
        lines.append("---")
        lines.append("")

        # Add personal development analysis
        personal_dev = self._fallback_personal_development(reviews)
        lines.extend(self._render_personal_development(personal_dev, reviews))

        def _render_points(title: str, emoji: str, entries: List[tuple[StoredReview, ReviewPoint]]) -> None:
            lines.append(f"## {emoji} {title}")
            lines.append("")
            if not entries:
                lines.append("수집된 항목이 없습니다.")
                lines.append("")
                return

            lines.append(f"| {title} | 근거/내용 | 링크 |")
            lines.append("|--------|-----------|------|")
            for review, point in entries:
                category = f"**PR #{review.number}**<br>`{review.title}`"

                # Combine message and example
                content_parts = [point.message]
                if point.example:
                    content_parts.append(f"<br>💡 **예시:**<br>`{point.example}`")
                content = "".join(content_parts)

                # Create link
                link_cell = f"[PR #{review.number}]({review.html_url})" if review.html_url else "-"
                lines.append(f"| {category} | {content} | {link_cell} |")
            lines.append("")
            lines.append("---")
            lines.append("")

        strength_entries: List[tuple[StoredReview, ReviewPoint]] = []
        improvement_entries: List[tuple[StoredReview, ReviewPoint]] = []

        for review in reviews:
            strength_entries.extend((review, point) for point in review.strengths)
            improvement_entries.extend((review, point) for point in review.improvements)

        _render_points("장점", "✨", strength_entries[:8])
        _render_points("보완점", "💡", improvement_entries[:8])

        lines.append("## 🌱 올해 성장한 점")
        lines.append("")
        growth_items = [review for review in reviews if review.overview]
        if not growth_items:
            lines.append("- 개별 리뷰 요약이 없어 성장 포인트를 추론하기 어렵습니다.")
        else:
            for i, review in enumerate(growth_items[:8], 1):
                lines.append(f"{i}. **PR #{review.number}** `{review.title}`")
                lines.append(f"   - {review.overview}")
                lines.append("")
        lines.append("---")
        lines.append("")

        lines.append("## 🎊 전체 총평")
        lines.append("")
        lines.append(
            "저장된 리뷰 요약을 바탕으로 팀이 지속해서 지식을 공유하고 있으며, "
            "통합 보고서를 통해 반복되는 강점과 개선점을 추적할 수 있습니다. "
            f"총 {len(reviews)}건의 PR을 통해 꾸준한 성장을 이어가고 있습니다."
        )
        lines.append("")
        lines.append("---")
        lines.append("")

        lines.append("## 📝 개별 PR 하이라이트")
        lines.append("")
        for i, review in enumerate(reviews, 1):
            date_str = review.created_at.strftime("%Y-%m-%d")
            highlight = f"{i}. **PR #{review.number}** `{review.title}` ({date_str})"
            lines.append(highlight)
            if review.html_url:
                lines.append(f"   - 🔗 [{review.html_url}]({review.html_url})")
            lines.append("")

        return "\n".join(lines).strip()

    def _generate_report_text(self, repo: str, reviews: List[StoredReview]) -> str:
        if not self.llm:
            return self._fallback_report(repo, reviews)

        context = self._build_prompt_context(repo, reviews)

        messages = [
            {
                "role": "system",
                "content": (
                    "당신은 기술 리더로서 팀 단위의 코드 리뷰 활동을 분석하는 통합 보고서를 작성합니다.\n\n"
                    "**보고서 목적:**\n"
                    "1. PR 리뷰 활동의 전체적 흐름과 패턴 파악\n"
                    "2. 팀 협업 및 지식 공유 현황 평가\n"
                    "3. 리뷰 프로세스 개선 기회 식별\n"
                    "4. 다음 분기 팀 목표 수립 근거 제공\n\n"
                    "**중요: 개인의 기술적 강점/약점은 분석하지 마세요.** "
                    "(별도의 개인 성장 분석이 이미 제공됩니다.) "
                    "대신 **팀 전체의 협업 패턴, 리뷰 문화, 프로세스 효율성**에 집중하세요.\n\n"
                    "**분석 관점:**\n"
                    "- PR 리뷰의 양적/질적 트렌드\n"
                    "- 팀 간 협업 활발도 및 지식 공유 정도\n"
                    "- 리뷰 프로세스의 병목 지점\n"
                    "- 반복되는 리뷰 패턴 (긍정적/부정적)\n"
                    "- 팀 문화 및 커뮤니케이션 특성\n\n"
                    "**보고서 구조:**\n\n"
                    "# 🎯 통합 코드 리뷰 보고서\n\n"
                    "## 📊 리뷰 활동 요약\n"
                    "- 전체 PR 수 및 기간별 분포\n"
                    "- 평균 리뷰 시간, 병합까지 소요 시간\n"
                    "- 주요 활동 트렌드 (증가/감소/안정)\n\n"
                    "## 🤝 협업 및 지식 공유\n"
                    "- 리뷰 참여 분포 (집중도 vs 분산도)\n"
                    "- 지식 공유 활성화 정도\n"
                    "- 팀 간 커뮤니케이션 패턴\n\n"
                    "## 🔄 프로세스 효율성\n"
                    "- 병목 구간 식별\n"
                    "- 리뷰 반응 속도\n"
                    "- 재작업(rework) 빈도와 원인\n\n"
                    "## 📈 주요 변화 및 트렌드\n"
                    "- 이전 기간 대비 변화\n"
                    "- 반복되는 리뷰 패턴\n"
                    "- 새롭게 나타난 특징\n\n"
                    "## 🎯 프로세스 개선 제안\n"
                    "1. 즉시 실행 가능한 개선사항 (1-3개)\n"
                    "2. 중기 개선 목표 (1-2개월)\n"
                    "3. 장기 투자 영역\n\n"
                    "## 📝 주요 PR 사례\n"
                    "- 팀에 학습 가치가 높았던 리뷰\n"
                    "- 협업의 모범 사례\n\n"
                    "**작성 원칙:**\n"
                    "- 팀 단위 관점 유지 (개인 평가 지양)\n"
                    "- 구체적 데이터와 예시 활용\n"
                    "- 건설적이고 실행 가능한 제안\n"
                    "- 팀 맥락과 문화 고려\n\n"
                    "출력은 Markdown 형식, 이모지는 적절히 사용하세요. 모든 응답은 한국어로 작성하세요."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"다음 PR 리뷰 데이터를 분석하여 팀 단위의 통합 보고서를 작성하세요:\n\n"
                    f"{context}\n\n"
                    "특히 다음 관점에서 분석해주세요:\n"
                    "1. 이 기간 동안 팀의 리뷰 활동에서 가장 큰 변화는?\n"
                    "2. 협업 및 지식 공유가 가장 활발한 영역은?\n"
                    "3. 리뷰 프로세스에서 개선이 필요한 부분은?\n"
                    "4. 다음 분기에 팀이 집중해야 할 목표는?"
                ),
            },
        ]

        try:
            content = self.llm.complete(messages, temperature=0.4)
            if content.strip():
                return content.strip()
        except Exception as exc:  # pragma: no cover - network errors hard to simulate
            console.log("LLM 통합 보고서 생성 실패", str(exc))

        return self._fallback_report(repo, reviews)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def create_integrated_report(self, repo: str) -> Path:
        """Create or refresh the integrated review report for a repository."""

        repo_input = repo.strip()
        if not repo_input:
            raise ValueError("Repository cannot be empty")

        reviews = self._load_reviews(repo_input)
        if not reviews:
            raise ValueError("No review summaries found for the given repository")

        # Generate personal development analysis
        console.log("개인 성장 분석 생성 중...")
        personal_dev = self._analyze_personal_development(repo_input, reviews)

        # Generate main report
        console.log("통합 보고서 생성 중...")
        report_text = self._generate_report_text(repo_input, reviews)

        # If LLM report doesn't include personal development section, add it at the beginning
        if "## 👤 개인 성장 분석" not in report_text and "개인 성장 분석" not in report_text:
            lines = report_text.split("\n")
            # Find where to insert (after the header and initial metadata)
            insert_idx = 0
            for i, line in enumerate(lines):
                if line.startswith("---") or line.startswith("##"):
                    insert_idx = i
                    break

            # Insert personal development section
            personal_dev_lines = self._render_personal_development(personal_dev, reviews)
            lines = lines[:insert_idx] + personal_dev_lines + lines[insert_idx:]
            report_text = "\n".join(lines)

        # Save report
        repo_dir = self._repo_dir(repo_input)
        repo_dir.mkdir(parents=True, exist_ok=True)
        report_path = repo_dir / "integrated_report.md"
        report_path.write_text(report_text, encoding="utf-8")

        # Also save personal development analysis as JSON for programmatic access
        personal_dev_path = repo_dir / "personal_development.json"
        personal_dev_path.write_text(
            json.dumps(personal_dev.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        console.log(f"개인 성장 분석 저장: {personal_dev_path}")
        return report_path


__all__ = ["ReviewReporter", "StoredReview"]
