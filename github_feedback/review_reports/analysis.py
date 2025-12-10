"""LLM-based analysis for personal development insights."""

from __future__ import annotations

import json
from typing import List

from ..console import Console
from ..llm import LLMClient
from ..models import (
    GrowthIndicator,
    ImprovementArea,
    PersonalDevelopmentAnalysis,
    StrengthPoint,
    TLDRSummary,
)
from ..prompts import (
    get_personal_development_system_prompt,
    get_personal_development_user_prompt,
)
from .data_loader import StoredReview

console = Console()


class PersonalDevelopmentAnalyzer:
    """Analyze personal development from PR reviews using LLM."""

    def __init__(self, llm: LLMClient | None = None) -> None:
        self.llm = llm

    def analyze(self, repo: str, reviews: List[StoredReview]) -> PersonalDevelopmentAnalysis:
        """Analyze personal development based on PR reviews."""
        if not self.llm or not reviews:
            return self._fallback_analysis(reviews)

        try:
            messages = self._build_messages(repo, reviews)
            # Increased temperature from 0.4 to 0.6 for better response quality
            # Increased max_retries to 5 for more robust analysis
            content = self.llm.complete(messages, temperature=0.6, max_retries=5)
            data = json.loads(content)
            return self._build_analysis_from_llm(data)
        except Exception as exc:  # pragma: no cover
            console.log("LLM 개인 발전 분석 실패", str(exc))
            return self._fallback_analysis(reviews)

    def _build_messages(self, repo: str, reviews: List[StoredReview]) -> List[dict]:
        """Create LLM messages for personal development prompt."""
        context = self._build_prompt_context(repo, reviews)
        early_reviews, recent_reviews = self._split_reviews_for_growth(reviews)

        return [
            {
                "role": "system",
                "content": get_personal_development_system_prompt(),
            },
            {
                "role": "user",
                "content": get_personal_development_user_prompt(
                    context, len(early_reviews), len(recent_reviews)
                ),
            },
        ]

    def _build_prompt_context(self, repo: str, reviews: List[StoredReview]) -> str:
        """Build context string for LLM prompt."""
        lines: List[str] = []
        lines.append(f"Repository: {repo}")
        lines.append(f"총 리뷰 PR 수: {len(reviews)}")
        lines.append("")
        lines.append("Pull Request 요약:")

        for review in reviews:
            # Include code change metrics for better analysis
            code_metrics = f"+{review.additions}/-{review.deletions}, {review.changed_files}개 파일 변경"
            lines.append(
                f"- PR #{review.number} {review.title} (작성자: {review.author}, 생성일: {review.created_at.date()}, 코드 변경: {code_metrics})"
            )
            if review.html_url:
                lines.append(f"  URL: {review.html_url}")

            # Include PR body for analyzing description quality
            if review.body:
                body_preview = review.body[:1000] + "..." if len(review.body) > 1000 else review.body
                lines.append(f"  PR 설명: {body_preview}")

            if review.overview:
                lines.append(f"  Overview: {review.overview}")

            # Include review comments for tone analysis
            if review.review_comments:
                lines.append(f"  리뷰 코멘트 ({len(review.review_comments)}개):")
                for idx, comment in enumerate(review.review_comments[:15], 1):
                    comment_preview = comment[:500] + "..." if len(comment) > 500 else comment
                    lines.append(f"    {idx}. {comment_preview}")
                if len(review.review_comments) > 15:
                    lines.append(f"    ... 외 {len(review.review_comments) - 15}개 코멘트")

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

    @staticmethod
    def _split_reviews_for_growth(reviews: List[StoredReview]) -> tuple[List[StoredReview], List[StoredReview]]:
        """Split reviews into early and recent lists for growth analysis."""
        midpoint = len(reviews) // 2
        if midpoint <= 0:
            return [], reviews
        return reviews[:midpoint], reviews[midpoint:]

    def _build_analysis_from_llm(self, data: dict) -> PersonalDevelopmentAnalysis:
        """Convert parsed LLM response into domain objects."""
        if not isinstance(data, dict):  # pragma: no cover - defensive guard
            raise ValueError("LLM response must be a JSON object")

        return PersonalDevelopmentAnalysis(
            strengths=self._parse_strength_points(data.get("strengths", [])),
            improvement_areas=self._parse_improvement_areas(data.get("improvement_areas", [])),
            growth_indicators=self._parse_growth_indicators(data.get("growth_indicators", [])),
            tldr_summary=self._parse_tldr_summary(data.get("tldr_summary")),
        )

    def _parse_tldr_summary(self, payload: object) -> TLDRSummary | None:
        """Parse TL;DR summary from LLM response."""
        if not isinstance(payload, dict):
            return None
        return TLDRSummary(
            top_strength=str(payload.get("top_strength", "")),
            primary_focus=str(payload.get("primary_focus", "")),
            measurable_goal=str(payload.get("measurable_goal", "")),
        )

    def _parse_strength_points(self, payload: object) -> List[StrengthPoint]:
        """Parse strength points from LLM response."""
        points: List[StrengthPoint] = []
        if not isinstance(payload, list):
            return points
        for item in payload:
            if not isinstance(item, dict):
                continue
            points.append(
                StrengthPoint(
                    category=str(item.get("category", "기타")),
                    description=str(item.get("description", "")),
                    evidence=list(item.get("evidence", [])),
                    impact=str(item.get("impact", "medium")),
                )
            )
        return points

    def _parse_improvement_areas(self, payload: object) -> List[ImprovementArea]:
        """Parse improvement areas from LLM response."""
        areas: List[ImprovementArea] = []
        if not isinstance(payload, list):
            return areas
        for item in payload:
            if not isinstance(item, dict):
                continue
            areas.append(
                ImprovementArea(
                    category=str(item.get("category", "기타")),
                    description=str(item.get("description", "")),
                    evidence=list(item.get("evidence", [])),
                    suggestions=list(item.get("suggestions", [])),
                    priority=str(item.get("priority", "medium")),
                )
            )
        return areas

    def _parse_growth_indicators(self, payload: object) -> List[GrowthIndicator]:
        """Parse growth indicators from LLM response."""
        indicators: List[GrowthIndicator] = []
        if not isinstance(payload, list):
            return indicators
        for item in payload:
            if not isinstance(item, dict):
                continue
            indicators.append(
                GrowthIndicator(
                    aspect=str(item.get("aspect", "")),
                    description=str(item.get("description", "")),
                    before_examples=list(item.get("before_examples", [])),
                    after_examples=list(item.get("after_examples", [])),
                    progress_summary=str(item.get("progress_summary", "")),
                )
            )
        return indicators

    def _fallback_analysis(self, reviews: List[StoredReview]) -> PersonalDevelopmentAnalysis:
        """Provide basic personal development analysis without LLM."""
        # Collect all strengths and improvements from reviews
        all_strengths: List[tuple[StoredReview, object]] = []
        all_improvements: List[tuple[StoredReview, object]] = []

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


__all__ = ["PersonalDevelopmentAnalyzer"]
