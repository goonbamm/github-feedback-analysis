"""Skill tree section builder."""

import html
from typing import List

from ..constants import REGEX_PATTERNS, SKILL_MASTERY
from ..game_elements import GameRenderer
from ..models import MetricSnapshot
from .base_builder import SectionBuilder


class SkillTreeBuilder(SectionBuilder):
    """Builder for skill tree section showing acquired and available skills."""

    def build(self) -> List[str]:
        """Build skill tree section.

        Returns:
            List of markdown lines for skill tree section
        """
        lines = ["## 🎮 스킬 트리", ""]
        lines.append("> 획득한 스킬과 습득 가능한 스킬을 확인하세요")
        lines.append("")

        # Collect acquired skills (from awards and highlights)
        acquired_skills = []
        available_skills = []
        growing_skills = []

        # 1. Acquired Skills - from top awards and strengths
        if self.metrics.awards:
            max_awards = SKILL_MASTERY['max_top_awards_for_skills']
            for award in self.metrics.awards[:max_awards]:
                # Determine mastery based on award position
                base_mastery = SKILL_MASTERY['base_mastery']
                reduction = SKILL_MASTERY['mastery_reduction_per_rank']
                mastery = base_mastery - (self.metrics.awards.index(award) * reduction)

                # Extract skill name from award by removing emoji and trimming
                # Award format: "🏆 Award Name - Description"
                skill_name = award
                # Remove leading emoji and spaces
                skill_name = REGEX_PATTERNS['emoji_prefix'].sub('', skill_name)
                # Take content before " - " if exists, otherwise use first N chars
                if ' - ' in skill_name:
                    skill_name = skill_name.split(' - ')[0].strip()
                # Limit to configured max length
                max_len = SKILL_MASTERY['skill_name_max_length']
                skill_name = skill_name[:max_len].rstrip('.,!? ') if len(skill_name) > max_len else skill_name

                acquired_skills.append({
                    "name": skill_name,
                    "type": "패시브",
                    "mastery": mastery,
                    "effect": award,  # Full award as effect description
                    "evidence": [award],
                    "emoji": "🏆"
                })

        # Add skills from highlights
        max_skills = SKILL_MASTERY['max_skills_total']
        if self.metrics.highlights and len(acquired_skills) < max_skills:
            remaining = max_skills - len(acquired_skills)
            for highlight in self.metrics.highlights[:remaining]:
                # Extract first sentence and limit to configured max length
                first_sentence = highlight.split('.')[0]
                max_len = SKILL_MASTERY['skill_name_max_length']
                skill_name = first_sentence[:max_len].rstrip('.,!? ') if len(first_sentence) > max_len else first_sentence

                acquired_skills.append({
                    "name": skill_name,
                    "type": "액티브",
                    "mastery": SKILL_MASTERY['highlight_mastery'],
                    "effect": highlight,  # Full highlight as effect description
                    "evidence": [highlight],
                    "emoji": "✨"
                })

        # Add coding habits as acquired skills (always show, regardless of quality)
        # These are shown separately in communication skills section
        communication_skills = []
        if self.metrics.detailed_feedback:
            # Commit message mastery - always show if data exists
            if self.metrics.detailed_feedback.commit_feedback:
                cf = self.metrics.detailed_feedback.commit_feedback
                if cf.total_commits > 0:
                    quality_ratio = cf.good_messages / cf.total_commits
                    base_mastery = SKILL_MASTERY['base_mastery']
                    mastery = min(base_mastery, int(quality_ratio * base_mastery))

                    # Determine skill level and name
                    if quality_ratio >= SKILL_MASTERY['excellent_quality_ratio']:
                        skill_name = "커밋 스토리텔링 마스터"
                        skill_type = "전설"
                    elif quality_ratio >= SKILL_MASTERY['good_quality_ratio']:
                        skill_name = "커밋 메시지 장인"
                        skill_type = "숙련"
                    else:
                        skill_name = "커밋 작성 견습생"
                        skill_type = "수련중"

                    communication_skills.append({
                        "name": skill_name,
                        "type": skill_type,
                        "mastery": mastery,
                        "effect": f"전체 커밋의 {int(quality_ratio * 100)}%가 명확한 메시지",
                        "evidence": [f"{cf.good_messages}/{cf.total_commits} 커밋"],
                        "emoji": "📜"
                    })

            # PR title mastery - always show if data exists
            if self.metrics.detailed_feedback.pr_title_feedback:
                pf = self.metrics.detailed_feedback.pr_title_feedback
                if pf.total_prs > 0:
                    quality_ratio = pf.clear_titles / pf.total_prs
                    mastery = min(100, int(quality_ratio * 100))

                    # Determine skill level and name
                    if quality_ratio >= 0.8:
                        skill_name = "PR 타이틀 아티스트"
                        skill_type = "전설"
                    elif quality_ratio >= 0.6:
                        skill_name = "PR 네이밍 전문가"
                        skill_type = "숙련"
                    else:
                        skill_name = "PR 제목 학습자"
                        skill_type = "수련중"

                    communication_skills.append({
                        "name": skill_name,
                        "type": skill_type,
                        "mastery": mastery,
                        "effect": f"전체 PR의 {int(quality_ratio * 100)}%가 명확하고 구체적",
                        "evidence": [f"{pf.clear_titles}/{pf.total_prs} PR"],
                        "emoji": "🎯"
                    })

            # Review tone mastery - always show if data exists
            if self.metrics.detailed_feedback.review_tone_feedback:
                rtf = self.metrics.detailed_feedback.review_tone_feedback
                total_reviews = rtf.constructive_reviews + rtf.harsh_reviews + rtf.neutral_reviews
                if total_reviews > 0:
                    quality_ratio = rtf.constructive_reviews / total_reviews
                    mastery = min(100, int(quality_ratio * 100))

                    # Determine skill level and name
                    if quality_ratio >= 0.8:
                        skill_name = "코드 멘토링 거장"
                        skill_type = "전설"
                    elif quality_ratio >= 0.6:
                        skill_name = "건설적 리뷰어"
                        skill_type = "숙련"
                    else:
                        skill_name = "리뷰 커뮤니케이터"
                        skill_type = "수련중"

                    communication_skills.append({
                        "name": skill_name,
                        "type": skill_type,
                        "mastery": mastery,
                        "effect": f"전체 리뷰의 {int(quality_ratio * 100)}%가 건설적이고 도움이 됨",
                        "evidence": [f"{rtf.constructive_reviews}/{total_reviews} 리뷰"],
                        "emoji": "💬"
                    })

            # Issue description quality - always show if data exists
            if self.metrics.detailed_feedback.issue_feedback:
                isf = self.metrics.detailed_feedback.issue_feedback
                if isf.total_issues > 0:
                    quality_ratio = isf.well_described / isf.total_issues
                    mastery = min(100, int(quality_ratio * 100))

                    # Determine skill level and name
                    if quality_ratio >= 0.8:
                        skill_name = "이슈 문서화 전문가"
                        skill_type = "전설"
                    elif quality_ratio >= 0.6:
                        skill_name = "이슈 작성 숙련자"
                        skill_type = "숙련"
                    else:
                        skill_name = "이슈 보고 학습자"
                        skill_type = "수련중"

                    communication_skills.append({
                        "name": skill_name,
                        "type": skill_type,
                        "mastery": mastery,
                        "effect": f"전체 이슈의 {int(quality_ratio * 100)}%가 명확하고 재현 가능",
                        "evidence": [f"{isf.well_described}/{isf.total_issues} 이슈"],
                        "emoji": "📋"
                    })

        # Add top communication skills to acquired skills if quality is high (60%+)
        for comm_skill in communication_skills:
            if comm_skill["mastery"] >= 60 and len(acquired_skills) < 8:
                acquired_skills.append(comm_skill)

        # 2. Available Skills - from improvement suggestions
        if self.metrics.detailed_feedback:
            if self.metrics.detailed_feedback.commit_feedback and hasattr(self.metrics.detailed_feedback.commit_feedback, 'suggestions'):
                for idx, suggestion in enumerate(self.metrics.detailed_feedback.commit_feedback.suggestions[:2], 1):
                    # Generate skill name from suggestion content (first 50 chars or meaningful phrase)
                    skill_name = suggestion[:50].rstrip('.,!? ') if len(suggestion) > 50 else suggestion.rstrip('.,!? ')
                    available_skills.append({
                        "name": skill_name,
                        "type": "미습득",
                        "mastery": 40,
                        "effect": f"커밋 메시지 개선: {suggestion}",
                        "evidence": [suggestion],
                        "emoji": "📝"
                    })

            if self.metrics.detailed_feedback.pr_title_feedback and hasattr(self.metrics.detailed_feedback.pr_title_feedback, 'suggestions'):
                for idx, suggestion in enumerate(self.metrics.detailed_feedback.pr_title_feedback.suggestions[:2], 1):
                    # Generate skill name from suggestion content
                    skill_name = suggestion[:50].rstrip('.,!? ') if len(suggestion) > 50 else suggestion.rstrip('.,!? ')
                    available_skills.append({
                        "name": skill_name,
                        "type": "미습득",
                        "mastery": 40,
                        "effect": f"PR 제목 개선: {suggestion}",
                        "evidence": [suggestion],
                        "emoji": "🎯"
                    })

            if self.metrics.detailed_feedback.review_tone_feedback and hasattr(self.metrics.detailed_feedback.review_tone_feedback, 'suggestions'):
                for idx, suggestion in enumerate(self.metrics.detailed_feedback.review_tone_feedback.suggestions[:2], 1):
                    # Generate skill name from suggestion content
                    skill_name = suggestion[:50].rstrip('.,!? ') if len(suggestion) > 50 else suggestion.rstrip('.,!? ')
                    available_skills.append({
                        "name": skill_name,
                        "type": "미습득",
                        "mastery": 40,
                        "effect": f"리뷰 톤 개선: {suggestion}",
                        "evidence": [suggestion],
                        "emoji": "💬"
                    })

        # 3. Growing Skills - from retrospective positive patterns
        if self.metrics.retrospective and hasattr(self.metrics.retrospective, 'behavior_patterns'):
            positive_patterns = [bp for bp in self.metrics.retrospective.behavior_patterns if bp.impact == "positive"]
            for pattern in positive_patterns[:3]:
                growing_skills.append({
                    "name": pattern.description,
                    "type": "성장중",
                    "mastery": 60,
                    "effect": "빠르게 발전하고 있는 영역",
                    "evidence": [pattern.description],
                    "emoji": "🌱"
                })

        # Render all skills in one consolidated table
        lines.extend(GameRenderer.render_skill_tree_table(
            acquired_skills=acquired_skills,
            growing_skills=growing_skills,
            available_skills=available_skills[:3]  # Limit to top 3
        ))

        # Add Communication Skills section if data exists
        if communication_skills:
            lines.append("### 💬 커뮤니케이션 스킬")
            lines.append("")
            lines.append("> 커밋, PR, 리뷰, 이슈 등 협업을 위한 커뮤니케이션 능력")
            lines.append("")

            # Render communication skills as a separate table
            headers = ["스킬명", "숙련도", "효과", "통계"]
            rows = []

            for skill in communication_skills:
                mastery_bar = f'<div style="background: #e5e7eb; border-radius: 4px; height: 20px; width: 150px;"><div style="background: linear-gradient(90deg, #10b981 0%, #059669 100%); height: 100%; width: {skill["mastery"]}%; border-radius: 4px; box-shadow: 0 0 10px rgba(16, 185, 129, 0.3);"></div></div>'

                skill_name = html.escape(skill.get("name", ""), quote=False)
                skill_type = html.escape(skill.get("type", ""), quote=False)
                effect_cell = html.escape(skill.get("effect", ""), quote=False)
                evidence_values = skill.get("evidence", []) or []
                evidence_cell = "<br>".join(html.escape(ev, quote=False) for ev in evidence_values)

                skill_name_cell = f'{skill.get("emoji", "💬")} <strong>{skill_name}</strong><br><span style="color: #6b7280; font-size: 0.85em;">[{skill_type}]</span>'
                mastery_cell = f'{mastery_bar}<div style="margin-top: 4px; text-align: center; font-size: 0.85em; color: #4b5563;">{skill["mastery"]}%</div>'

                rows.append([skill_name_cell, mastery_cell, effect_cell, evidence_cell])

            lines.extend(GameRenderer.render_html_table(
                headers=headers,
                rows=rows,
                title="",
                description="",
                striped=True,
                escape_cells=False
            ))
            lines.append("")

        lines.append("---")
        lines.append("")
        return lines
