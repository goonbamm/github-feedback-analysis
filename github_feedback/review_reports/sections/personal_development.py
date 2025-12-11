"""Personal development section rendering."""

from __future__ import annotations

import re
from typing import List

from ...core.constants import REGEX_PATTERNS
from ...game_elements import GameRenderer
from ...core.models import PersonalDevelopmentAnalysis
from ..data_loader import StoredReview

# Legacy alias for backward compatibility
PR_NUMBER_PATTERN = REGEX_PATTERNS["pr_number"]


def render_personal_development(
    analysis: PersonalDevelopmentAnalysis, reviews: List[StoredReview]
) -> List[str]:
    """Render personal development analysis section with simplified structure."""
    lines: List[str] = []
    lines.append("## 👤 개인 피드백 리포트")
    lines.append("")

    # 1. TLDR section (30초 요약)
    lines.extend(_render_tldr_section(analysis))
    lines.append("---")
    lines.append("")

    pr_map = {review.number: review for review in reviews}

    # 2. Skill Tree (스킬 트리로 모든 정보 통합)
    lines.extend(_render_skill_tree_section(analysis, pr_map))

    return lines


def _render_tldr_section(analysis: PersonalDevelopmentAnalysis) -> List[str]:
    """Render 30-second summary section."""
    lines: List[str] = []
    if not analysis.tldr_summary:
        return lines

    lines.append("## ⚡ 30초 요약 (TL;DR)")
    lines.append("")
    lines.append(f"- ✅ **가장 잘하고 있는 것**: {analysis.tldr_summary.top_strength}")
    lines.append(f"- 🎯 **이번 달 집중할 것**: {analysis.tldr_summary.primary_focus}")
    lines.append(f"- 📈 **측정 목표**: {analysis.tldr_summary.measurable_goal}")
    lines.append("")
    return lines


def _render_skill_tree_section(
    analysis: PersonalDevelopmentAnalysis, pr_map: dict[int, StoredReview]
) -> List[str]:
    """Render skill tree section with consolidated table."""
    lines: List[str] = []
    lines.append("## 🎮 스킬 트리")
    lines.append("")
    lines.append("> 획득한 스킬과 습득 가능한 스킬을 확인하세요")
    lines.append("")

    # Collect all skills
    acquired_skills = []
    growing_skills = []
    available_skills = []

    # 1. Acquired Skills (from strengths)
    if analysis.strengths:
        for strength in analysis.strengths[:5]:  # Top 5 strengths
            # Calculate mastery based on impact
            mastery = {"high": 90, "medium": 75, "low": 60}.get(strength.impact, 70)

            # Determine skill type based on category
            skill_type = "패시브" if "품질" in strength.category or "코드" in strength.category else "액티브"

            # Get skill emoji based on category
            category_emojis = {
                "코드 품질": "💻",
                "협업": "🤝",
                "문서화": "📝",
                "테스트": "🧪",
                "설계": "🏗️",
            }
            skill_emoji = next(
                (emoji for key, emoji in category_emojis.items() if key in strength.category), "💎"
            )

            acquired_skills.append(
                {
                    "name": strength.category,
                    "type": skill_type,
                    "mastery": mastery,
                    "effect": strength.description,
                    "evidence": strength.evidence[:5],
                    "emoji": skill_emoji,
                }
            )

    # 2. Growing Skills (from growth indicators)
    if analysis.growth_indicators:
        for growth in analysis.growth_indicators[:3]:  # Top 3 growth areas
            # 성장 증거 준비
            growth_evidence = []
            if growth.progress_summary:
                growth_evidence.append(growth.progress_summary)
            if growth.before_examples:
                growth_evidence.append(f"Before: {growth.before_examples[0]}")
            if growth.after_examples:
                growth_evidence.append(f"After: {growth.after_examples[0]}")

            growing_skills.append(
                {
                    "name": growth.aspect,
                    "type": "성장중",
                    "mastery": 65,  # Growing skills are around 65%
                    "effect": growth.description,
                    "evidence": growth_evidence[:5],
                    "emoji": "🌱",
                }
            )

    # 3. Available Skills (from improvement areas)
    if analysis.improvement_areas:
        # Sort by priority
        priority_order = {"critical": 0, "important": 1, "nice-to-have": 2}
        sorted_improvements = sorted(
            analysis.improvement_areas[:3],  # Top 3
            key=lambda area: priority_order.get(area.priority, 1),
        )

        for area in sorted_improvements:
            # Calculate mastery based on priority (lower for more critical)
            mastery = {"critical": 30, "important": 40, "nice-to-have": 50}.get(area.priority, 40)

            # Get skill emoji based on category
            category_emojis = {
                "코드 품질": "💻",
                "커밋": "📝",
                "PR": "🔀",
                "리뷰": "👀",
                "테스트": "🧪",
            }
            skill_emoji = next((emoji for key, emoji in category_emojis.items() if key in area.category), "🎯")

            # 개선 제안 또는 증거 준비
            improvement_evidence = []
            if area.suggestions:
                improvement_evidence.extend(area.suggestions[:5])
            elif area.evidence:
                improvement_evidence.extend(area.evidence[:5])

            available_skills.append(
                {
                    "name": area.category,
                    "type": "미습득",
                    "mastery": mastery,
                    "effect": area.description,
                    "evidence": improvement_evidence,
                    "emoji": skill_emoji,
                }
            )

    # Render all skills in one consolidated table
    lines.extend(
        GameRenderer.render_skill_tree_table(
            acquired_skills=acquired_skills, growing_skills=growing_skills, available_skills=available_skills
        )
    )

    lines.append("---")
    lines.append("")
    return lines


__all__ = ["render_personal_development"]
