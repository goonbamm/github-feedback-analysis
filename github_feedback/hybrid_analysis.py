"""Hybrid analysis combining LLM and heuristic approaches."""

from __future__ import annotations

import logging
from typing import Any

from .core.constants import VALIDATION_THRESHOLDS

logger = logging.getLogger(__name__)


class HybridAnalyzer:
    """Combines LLM and heuristic analysis for robustness."""

    @staticmethod
    def merge_strength_evidence(
        llm_strength: dict[str, Any],
        heuristic_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Merge LLM strength with heuristic data for better evidence.

        Args:
            llm_strength: Strength item from LLM
            heuristic_data: Heuristic analysis results

        Returns:
            Enhanced strength with additional evidence
        """
        enhanced = llm_strength.copy()

        # If LLM evidence is weak, supplement with heuristic evidence
        evidence = enhanced.get("evidence", [])

        if len(evidence) < VALIDATION_THRESHOLDS['min_evidence_count']:  # Weak evidence
            # Add heuristic examples as evidence
            if "examples_good" in heuristic_data:
                for example in heuristic_data["examples_good"][:2]:
                    if "message" in example and "reason" in example:
                        evidence.append(
                            f"발견된 좋은 예: '{example['message']}' - {example['reason']}"
                        )

            enhanced["evidence"] = evidence

        return enhanced

    @staticmethod
    def merge_improvement_suggestions(
        llm_improvement: dict[str, Any],
        heuristic_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Merge LLM improvement area with heuristic suggestions.

        Args:
            llm_improvement: Improvement area from LLM
            heuristic_data: Heuristic analysis results

        Returns:
            Enhanced improvement with additional suggestions
        """
        enhanced = llm_improvement.copy()

        # If LLM suggestions are generic, supplement with heuristic suggestions
        suggestions = enhanced.get("suggestions", [])

        if len(suggestions) < VALIDATION_THRESHOLDS['min_evidence_count']:  # Weak suggestions
            # Add heuristic suggestions
            if "suggestions" in heuristic_data:
                for sugg in heuristic_data["suggestions"][:3]:
                    if sugg not in suggestions:
                        suggestions.append(sugg)

            enhanced["suggestions"] = suggestions

        return enhanced

    @staticmethod
    def create_hybrid_commit_analysis(
        llm_result: dict[str, Any] | None,
        fallback_result: dict[str, Any],
        validation_score: float = 0.0
    ) -> dict[str, Any]:
        """Create hybrid commit analysis combining LLM and heuristic results.

        Args:
            llm_result: LLM analysis result (None if failed)
            fallback_result: Heuristic fallback result
            validation_score: Quality score of LLM result (0-1)

        Returns:
            Hybrid analysis result
        """
        if llm_result is None or validation_score < VALIDATION_THRESHOLDS['poor']:
            # LLM failed or very low quality, use pure heuristic
            logger.info("Using pure heuristic analysis (LLM unavailable or low quality)")
            return fallback_result

        if validation_score < VALIDATION_THRESHOLDS['acceptable']:
            # LLM quality is low, create hybrid
            logger.info("Creating hybrid analysis (LLM quality below threshold)")

            hybrid = {
                "good_messages": llm_result.get("good_messages", fallback_result.get("good_messages", 0)),
                "poor_messages": llm_result.get("poor_messages", fallback_result.get("poor_messages", 0)),
                "suggestions": [],
                "examples_good": llm_result.get("examples_good", []),
                "examples_poor": llm_result.get("examples_poor", []),
            }

            # Combine suggestions (LLM first, then heuristic)
            llm_suggestions = llm_result.get("suggestions", [])
            heuristic_suggestions = fallback_result.get("suggestions", [])

            # Add LLM suggestions
            for sugg in llm_suggestions:
                if len(sugg) > VALIDATION_THRESHOLDS['min_substantial_length']:  # Only add substantial suggestions
                    hybrid["suggestions"].append(sugg)

            # Fill remaining slots with heuristic suggestions
            for sugg in heuristic_suggestions:
                if sugg not in hybrid["suggestions"] and len(hybrid["suggestions"]) < VALIDATION_THRESHOLDS['max_hybrid_suggestions']:
                    hybrid["suggestions"].append(sugg)

            # If LLM examples are weak, supplement with heuristic
            if len(hybrid["examples_good"]) < VALIDATION_THRESHOLDS['min_evidence_count']:
                for ex in fallback_result.get("examples_good", [])[:3]:
                    if ex not in hybrid["examples_good"]:
                        hybrid["examples_good"].append(ex)

            if len(hybrid["examples_poor"]) < VALIDATION_THRESHOLDS['min_evidence_count']:
                for ex in fallback_result.get("examples_poor", [])[:3]:
                    if ex not in hybrid["examples_poor"]:
                        hybrid["examples_poor"].append(ex)

            return hybrid

        # LLM quality is good, use it
        logger.info("Using LLM analysis (high quality)")
        return llm_result

    @staticmethod
    def validate_and_enhance_personal_development(
        llm_result: dict[str, Any],
        validation_result: Any,  # ValidationResult
        pr_titles: list[dict[str, str]],
    ) -> dict[str, Any]:
        """Validate and enhance personal development analysis.

        Args:
            llm_result: LLM analysis result
            validation_result: Validation result with quality score
            pr_titles: Original PR titles for fallback enhancement

        Returns:
            Enhanced or hybrid result
        """
        if validation_result.score >= VALIDATION_THRESHOLDS['strong']:
            # High quality, return as is
            return llm_result

        if validation_result.score < VALIDATION_THRESHOLDS['weak']:
            # Very low quality, log warning
            logger.warning(
                f"Personal development analysis quality very low ({validation_result.score:.2f}). "
                "Consider reviewing LLM output."
            )

        # Medium quality: enhance with basic heuristics
        enhanced = llm_result.copy()

        # Ensure minimum suggestions in improvement areas
        for area in enhanced.get("improvement_areas", []):
            suggestions = area.get("suggestions", [])
            if len(suggestions) < VALIDATION_THRESHOLDS['min_evidence_count']:
                # Add generic but actionable suggestion
                category = area.get("category", "")
                if "PR 제목" in category or "title" in category.lower():
                    suggestions.append(
                        "다음 5개 PR에서 feat/fix/refactor prefix를 일관되게 사용하고 "
                        "구체적인 변경 내용을 15자 이상으로 작성하기"
                    )
                elif "설명" in category or "description" in category.lower():
                    suggestions.append(
                        "PR 템플릿 활용: ## 변경 이유, ## 구현 방법, ## 테스트 계획 섹션 포함하기"
                    )
                elif "리뷰" in category or "review" in category.lower():
                    suggestions.append(
                        "리뷰 코멘트 작성 시 '~하면 어떨까요?'와 같은 제안형 표현 사용하고 "
                        "구체적인 예시나 대안 제시하기"
                    )

                area["suggestions"] = suggestions

        return enhanced


__all__ = ["HybridAnalyzer"]
