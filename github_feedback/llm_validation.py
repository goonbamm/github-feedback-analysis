"""Validation utilities for LLM responses to ensure quality and consistency."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class ValidationResult:
    """Result of LLM response validation."""

    is_valid: bool
    score: float  # 0.0 to 1.0
    issues: list[str]
    warnings: list[str]


class LLMResponseValidator:
    """Validates LLM responses for quality and completeness."""

    @staticmethod
    def validate_evidence_quality(evidence: list[str]) -> ValidationResult:
        """Validate that evidence contains quantitative data and specific examples.

        Args:
            evidence: List of evidence strings

        Returns:
            ValidationResult with quality score and issues
        """
        if not evidence:
            return ValidationResult(
                is_valid=False,
                score=0.0,
                issues=["Evidence list is empty"],
                warnings=[],
            )

        issues = []
        warnings = []
        score_components = []

        for idx, item in enumerate(evidence, 1):
            item_score = 0.0
            item_issues = []

            # Check for PR number references
            if re.search(r'PR\s*#\d+', item):
                item_score += 0.25
            else:
                item_issues.append(f"Evidence {idx} lacks PR number reference")

            # Check for quantitative data (percentages, counts, metrics)
            quantitative_patterns = [
                r'\d+%',  # Percentages
                r'\d+개',  # Count in Korean
                r'총\s*\d+',  # Total count
                r'\d+/\d+',  # Ratios
                r'[+\-]\d+줄',  # Code line changes
                r'\d+\.\d+',  # Decimal numbers
                r'\d+일',  # Days
                r'\d+회',  # Times/occurrences
            ]

            has_quantitative = any(re.search(pattern, item) for pattern in quantitative_patterns)
            if has_quantitative:
                item_score += 0.25
            else:
                item_issues.append(f"Evidence {idx} lacks quantitative data")

            # Check for quoted text (actual PR titles, descriptions, or comments)
            if re.search(r'[\'"].*?[\'"]|「.*?」', item):
                item_score += 0.25
            else:
                warnings.append(f"Evidence {idx} could include quoted text for specificity")

            # Check minimum length (should be descriptive)
            if len(item) >= 20:
                item_score += 0.25
            else:
                item_issues.append(f"Evidence {idx} is too short ({len(item)} chars)")

            score_components.append(item_score)
            issues.extend(item_issues)

        # Calculate overall score
        avg_score = sum(score_components) / len(score_components) if score_components else 0.0

        # Determine validity (at least 50% of items should be good quality)
        is_valid = avg_score >= 0.5

        return ValidationResult(
            is_valid=is_valid,
            score=avg_score,
            issues=issues,
            warnings=warnings,
        )

    @staticmethod
    def validate_category_specificity(category: str) -> ValidationResult:
        """Validate that category is specific, not generic.

        Args:
            category: Category string to validate

        Returns:
            ValidationResult with specificity score
        """
        issues = []
        warnings = []
        score = 1.0

        # Generic terms that should be avoided
        generic_terms = [
            '코드 품질',
            '개선 영역',
            '강점',
            '약점',
            '커뮤니케이션',
            '문서화',
            '테스트',
        ]

        # Check if category is too generic
        category_lower = category.lower()
        for term in generic_terms:
            if category_lower == term.lower():
                issues.append(f"Category is too generic: '{category}'")
                score = 0.0
                break

        # Category should be descriptive (longer)
        if len(category) < 10:
            warnings.append(f"Category is short ({len(category)} chars), consider more descriptive name")
            score *= 0.8

        # Good categories typically contain specific actions or patterns
        action_patterns = [
            r'명확한',
            r'일관된',
            r'구체적',
            r'체계적',
            r'효과적',
            r'분리',
            r'개선',
            r'향상',
            r'최적화',
        ]

        has_action = any(re.search(pattern, category) for pattern in action_patterns)
        if has_action:
            score = min(1.0, score + 0.2)

        is_valid = score >= 0.6

        return ValidationResult(
            is_valid=is_valid,
            score=score,
            issues=issues,
            warnings=warnings,
        )

    @staticmethod
    def validate_description_depth(description: str, min_sentences: int = 2) -> ValidationResult:
        """Validate that description is detailed enough.

        Args:
            description: Description text
            min_sentences: Minimum number of sentences required

        Returns:
            ValidationResult with depth score
        """
        issues = []
        warnings = []

        if not description:
            return ValidationResult(
                is_valid=False,
                score=0.0,
                issues=["Description is empty"],
                warnings=[],
            )

        # Count sentences (rough approximation)
        sentence_count = len(re.findall(r'[.!?。]\s+', description)) + 1

        if sentence_count < min_sentences:
            issues.append(
                f"Description has only {sentence_count} sentence(s), "
                f"minimum {min_sentences} required"
            )

        # Check for minimum length
        min_length = 50
        if len(description) < min_length:
            issues.append(f"Description is too short ({len(description)} chars, minimum {min_length})")

        # Calculate score based on length and sentence count
        length_score = min(1.0, len(description) / 100)  # Full score at 100+ chars
        sentence_score = min(1.0, sentence_count / min_sentences)
        score = (length_score + sentence_score) / 2

        is_valid = score >= 0.7 and sentence_count >= min_sentences

        return ValidationResult(
            is_valid=is_valid,
            score=score,
            issues=issues,
            warnings=warnings,
        )

    @staticmethod
    def validate_personal_development_response(data: dict[str, Any]) -> ValidationResult:
        """Validate complete personal development analysis response.

        Args:
            data: Parsed JSON response from LLM

        Returns:
            ValidationResult with overall quality assessment
        """
        issues = []
        warnings = []
        scores = []

        # Validate strengths
        strengths = data.get("strengths", [])
        if not strengths:
            issues.append("No strengths provided")
            scores.append(0.0)
        else:
            for idx, strength in enumerate(strengths, 1):
                # Validate category
                category_result = LLMResponseValidator.validate_category_specificity(
                    strength.get("category", "")
                )
                if not category_result.is_valid:
                    issues.extend([f"Strength {idx}: {issue}" for issue in category_result.issues])

                # Validate description
                desc_result = LLMResponseValidator.validate_description_depth(
                    strength.get("description", "")
                )
                if not desc_result.is_valid:
                    issues.extend([f"Strength {idx}: {issue}" for issue in desc_result.issues])

                # Validate evidence
                evidence_result = LLMResponseValidator.validate_evidence_quality(
                    strength.get("evidence", [])
                )
                if not evidence_result.is_valid:
                    warnings.extend([f"Strength {idx}: {warn}" for warn in evidence_result.warnings])
                    if evidence_result.score < 0.5:
                        issues.extend([f"Strength {idx}: {issue}" for issue in evidence_result.issues])

                # Calculate item score
                item_score = (category_result.score + desc_result.score + evidence_result.score) / 3
                scores.append(item_score)

        # Validate improvement areas
        improvement_areas = data.get("improvement_areas", [])
        if improvement_areas:
            for idx, area in enumerate(improvement_areas, 1):
                # Similar validation as strengths
                category_result = LLMResponseValidator.validate_category_specificity(
                    area.get("category", "")
                )
                desc_result = LLMResponseValidator.validate_description_depth(
                    area.get("description", "")
                )
                evidence_result = LLMResponseValidator.validate_evidence_quality(
                    area.get("evidence", [])
                )

                if not category_result.is_valid:
                    issues.extend([f"Improvement {idx}: {issue}" for issue in category_result.issues])
                if not desc_result.is_valid:
                    issues.extend([f"Improvement {idx}: {issue}" for issue in desc_result.issues])
                if evidence_result.score < 0.5:
                    warnings.extend([f"Improvement {idx}: {warn}" for warn in evidence_result.warnings])

                item_score = (category_result.score + desc_result.score + evidence_result.score) / 3
                scores.append(item_score)

        # Validate suggestions are actionable
        for idx, area in enumerate(improvement_areas, 1):
            suggestions = area.get("suggestions", [])
            if not suggestions:
                warnings.append(f"Improvement {idx} has no suggestions")
            else:
                for sugg in suggestions:
                    if len(sugg) < 20:
                        warnings.append(
                            f"Improvement {idx}: Suggestion is too brief ('{sugg}')"
                        )

        # Calculate overall score
        avg_score = sum(scores) / len(scores) if scores else 0.0

        # Determine validity threshold
        is_valid = avg_score >= 0.6 and len(issues) < 5

        return ValidationResult(
            is_valid=is_valid,
            score=avg_score,
            issues=issues,
            warnings=warnings,
        )


__all__ = ["ValidationResult", "LLMResponseValidator"]
