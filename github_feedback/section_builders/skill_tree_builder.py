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

        # Collect all skill types
        acquired_skills = self._collect_acquired_skills()
        communication_skills = self._collect_communication_skills()
        available_skills = self._collect_available_skills()
        growing_skills = self._collect_growing_skills()

        # Add top communication skills to acquired skills if quality is high (60%+)
        for comm_skill in communication_skills:
            if comm_skill["mastery"] >= 60 and len(acquired_skills) < 8:
                acquired_skills.append(comm_skill)

        # Render all skills in one consolidated table
        lines.extend(GameRenderer.render_skill_tree_table(
            acquired_skills=acquired_skills,
            growing_skills=growing_skills,
            available_skills=available_skills[:3]  # Limit to top 3
        ))

        # Add Communication Skills section if data exists
        if communication_skills:
            lines.extend(self._render_communication_skills_section(communication_skills))

        lines.append("---")
        lines.append("")
        return lines

    def _collect_acquired_skills(self) -> List[dict]:
        """Collect acquired skills from awards and highlights.

        Returns:
            List of skill dictionaries with name, type, mastery, effect, evidence
        """
        acquired_skills = []

        # From top awards
        if self.metrics.awards:
            max_awards = SKILL_MASTERY['max_top_awards_for_skills']
            for award in self.metrics.awards[:max_awards]:
                # Determine mastery based on award position
                base_mastery = SKILL_MASTERY['base_mastery']
                reduction = SKILL_MASTERY['mastery_reduction_per_rank']
                mastery = base_mastery - (self.metrics.awards.index(award) * reduction)

                # Extract skill name from award by removing emoji and trimming
                skill_name = self._extract_skill_name_from_text(award)

                acquired_skills.append({
                    "name": skill_name,
                    "type": "패시브",
                    "mastery": mastery,
                    "effect": award,
                    "evidence": [award],
                    "emoji": "🏆"
                })

        # From highlights
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
                    "effect": highlight,
                    "evidence": [highlight],
                    "emoji": "✨"
                })

        return acquired_skills

    def _extract_skill_name_from_text(self, text: str) -> str:
        """Extract skill name from text by removing emoji and trimming.

        Args:
            text: Text to extract skill name from (e.g., "🏆 Award Name - Description")

        Returns:
            Extracted skill name
        """
        # Remove leading emoji and spaces
        skill_name = REGEX_PATTERNS['emoji_prefix'].sub('', text)
        # Take content before " - " if exists
        if ' - ' in skill_name:
            skill_name = skill_name.split(' - ')[0].strip()
        # Limit to configured max length
        max_len = SKILL_MASTERY['skill_name_max_length']
        skill_name = skill_name[:max_len].rstrip('.,!? ') if len(skill_name) > max_len else skill_name
        return skill_name

    def _collect_communication_skills(self) -> List[dict]:
        """Collect communication skills from detailed feedback.

        Returns:
            List of communication skill dictionaries
        """
        communication_skills = []

        if not self.metrics.detailed_feedback:
            return communication_skills

        # Commit message mastery
        if self.metrics.detailed_feedback.commit_feedback:
            skill = self._create_commit_skill()
            if skill:
                communication_skills.append(skill)

        # PR title mastery
        if self.metrics.detailed_feedback.pr_title_feedback:
            skill = self._create_pr_title_skill()
            if skill:
                communication_skills.append(skill)

        # Review tone mastery
        if self.metrics.detailed_feedback.review_tone_feedback:
            skill = self._create_review_tone_skill()
            if skill:
                communication_skills.append(skill)

        # Issue description quality
        if self.metrics.detailed_feedback.issue_feedback:
            skill = self._create_issue_skill()
            if skill:
                communication_skills.append(skill)

        return communication_skills

    def _create_commit_skill(self) -> dict | None:
        """Create commit message skill from feedback data.

        Returns:
            Skill dictionary or None if insufficient data
        """
        cf = self.metrics.detailed_feedback.commit_feedback
        if cf.total_commits == 0:
            return None

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

        return {
            "name": skill_name,
            "type": skill_type,
            "mastery": mastery,
            "effect": f"전체 커밋의 {int(quality_ratio * 100)}%가 명확한 메시지",
            "evidence": [f"{cf.good_messages}/{cf.total_commits} 커밋"],
            "emoji": "📜"
        }

    def _create_pr_title_skill(self) -> dict | None:
        """Create PR title skill from feedback data.

        Returns:
            Skill dictionary or None if insufficient data
        """
        pf = self.metrics.detailed_feedback.pr_title_feedback
        if pf.total_prs == 0:
            return None

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

        return {
            "name": skill_name,
            "type": skill_type,
            "mastery": mastery,
            "effect": f"전체 PR의 {int(quality_ratio * 100)}%가 명확하고 구체적",
            "evidence": [f"{pf.clear_titles}/{pf.total_prs} PR"],
            "emoji": "🎯"
        }

    def _create_review_tone_skill(self) -> dict | None:
        """Create review tone skill from feedback data.

        Returns:
            Skill dictionary or None if insufficient data
        """
        rtf = self.metrics.detailed_feedback.review_tone_feedback
        total_reviews = rtf.constructive_reviews + rtf.harsh_reviews + rtf.neutral_reviews
        if total_reviews == 0:
            return None

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

        return {
            "name": skill_name,
            "type": skill_type,
            "mastery": mastery,
            "effect": f"전체 리뷰의 {int(quality_ratio * 100)}%가 건설적이고 도움이 됨",
            "evidence": [f"{rtf.constructive_reviews}/{total_reviews} 리뷰"],
            "emoji": "💬"
        }

    def _create_issue_skill(self) -> dict | None:
        """Create issue description skill from feedback data.

        Returns:
            Skill dictionary or None if insufficient data
        """
        isf = self.metrics.detailed_feedback.issue_feedback
        if isf.total_issues == 0:
            return None

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

        return {
            "name": skill_name,
            "type": skill_type,
            "mastery": mastery,
            "effect": f"전체 이슈의 {int(quality_ratio * 100)}%가 명확하고 재현 가능",
            "evidence": [f"{isf.well_described}/{isf.total_issues} 이슈"],
            "emoji": "📋"
        }

    def _collect_available_skills(self) -> List[dict]:
        """Collect available (not yet acquired) skills from improvement suggestions.

        Returns:
            List of available skill dictionaries
        """
        available_skills = []

        if not self.metrics.detailed_feedback:
            return available_skills

        # From commit feedback suggestions
        if self.metrics.detailed_feedback.commit_feedback and hasattr(self.metrics.detailed_feedback.commit_feedback, 'suggestions'):
            for suggestion in self.metrics.detailed_feedback.commit_feedback.suggestions[:2]:
                skill_name = suggestion[:50].rstrip('.,!? ') if len(suggestion) > 50 else suggestion.rstrip('.,!? ')
                available_skills.append({
                    "name": skill_name,
                    "type": "미습득",
                    "mastery": 40,
                    "effect": f"커밋 메시지 개선: {suggestion}",
                    "evidence": [suggestion],
                    "emoji": "📝"
                })

        # From PR title feedback suggestions
        if self.metrics.detailed_feedback.pr_title_feedback and hasattr(self.metrics.detailed_feedback.pr_title_feedback, 'suggestions'):
            for suggestion in self.metrics.detailed_feedback.pr_title_feedback.suggestions[:2]:
                skill_name = suggestion[:50].rstrip('.,!? ') if len(suggestion) > 50 else suggestion.rstrip('.,!? ')
                available_skills.append({
                    "name": skill_name,
                    "type": "미습득",
                    "mastery": 40,
                    "effect": f"PR 제목 개선: {suggestion}",
                    "evidence": [suggestion],
                    "emoji": "🎯"
                })

        # From review tone feedback suggestions
        if self.metrics.detailed_feedback.review_tone_feedback and hasattr(self.metrics.detailed_feedback.review_tone_feedback, 'suggestions'):
            for suggestion in self.metrics.detailed_feedback.review_tone_feedback.suggestions[:2]:
                skill_name = suggestion[:50].rstrip('.,!? ') if len(suggestion) > 50 else suggestion.rstrip('.,!? ')
                available_skills.append({
                    "name": skill_name,
                    "type": "미습득",
                    "mastery": 40,
                    "effect": f"리뷰 톤 개선: {suggestion}",
                    "evidence": [suggestion],
                    "emoji": "💬"
                })

        return available_skills

    def _collect_growing_skills(self) -> List[dict]:
        """Collect growing skills from retrospective positive patterns.

        Returns:
            List of growing skill dictionaries
        """
        growing_skills = []

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

        return growing_skills

    def _render_communication_skills_section(self, communication_skills: List[dict]) -> List[str]:
        """Render communication skills section as HTML table.

        Args:
            communication_skills: List of communication skill dictionaries

        Returns:
            List of markdown lines for communication skills section
        """
        lines = []
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

        return lines
