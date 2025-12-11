"""Retrospective section builder."""

import html
from typing import List

from ..core.constants import DISPLAY_LIMITS
from ..game_elements import GameRenderer
from ..core.models import MetricSnapshot
from ..section_builders.base_builder import SectionBuilder


class RetrospectiveBuilder(SectionBuilder):
    """Builder for comprehensive retrospective analysis section."""

    def build(self) -> List[str]:
        """Build retrospective section.

        Returns:
            List of markdown lines for retrospective section
        """
        if not self.metrics.retrospective:
            return []

        retro = self.metrics.retrospective

        # Build all subsections using dedicated methods
        subsections = []
        subsections.extend(self._build_time_comparisons_subsection(retro))
        subsections.extend(self._build_behavior_patterns_subsection(retro))
        subsections.extend(self._build_learning_insights_subsection(retro))
        subsections.extend(self._build_impact_assessments_subsection(retro))
        subsections.extend(self._build_collaboration_insights_subsection(retro))
        subsections.extend(self._build_balance_metrics_subsection(retro))
        subsections.extend(self._build_code_health_subsection(retro))
        subsections.extend(self._build_actionable_insights_subsection(retro))
        subsections.extend(self._build_areas_for_growth_subsection(retro))
        subsections.extend(self._build_narrative_subsection(retro))

        # If no subsections have content, don't create the section
        if not subsections:
            return []

        lines = ["## 🔍 Deep Retrospective Analysis", ""]
        lines.append("> 데이터 기반의 심층적인 회고와 인사이트")
        lines.append("")
        lines.extend(subsections)
        lines.append("---")
        lines.append("")
        return lines

    def _build_time_comparisons_subsection(self, retro) -> List[str]:
        """Build time comparisons subsection of retrospective (HTML version)."""
        lines = []
        if not retro.time_comparisons:
            return lines

        lines.append("### 📊 기간 비교 분석")
        lines.append("")
        lines.append("> 전반기와 후반기의 변화 추이를 비교합니다")
        lines.append("")

        # Build table data
        headers = ["지표", "전반기", "후반기", "변화량", "변화율", "의미"]
        rows = []
        for tc in retro.time_comparisons:
            direction_emoji = {"increasing": "📈", "decreasing": "📉"}.get(tc.direction, "➡️")
            significance_text = {
                "major": "큰 변화",
                "moderate": "중간 변화",
                "minor": "작은 변화"
            }.get(tc.significance, tc.significance)

            rows.append([
                tc.metric_name,
                f"{tc.previous_value:.1f}",
                f"{tc.current_value:.1f}",
                f"{tc.change_absolute:+.1f}",
                f"{tc.change_percentage:+.1f}%",
                f"{direction_emoji} {significance_text}"
            ])

        # Render as HTML table
        lines.extend(GameRenderer.render_html_table(
            headers=headers,
            rows=rows,
            title="",
            description="",
            striped=True
        ))

        return lines

    def _build_behavior_patterns_subsection(self, retro) -> List[str]:
        """Build behavior patterns subsection of retrospective (HTML version)."""
        lines = []
        if not retro.behavior_patterns:
            return lines

        lines.append("### 🧠 행동 패턴 분석")
        lines.append("")
        lines.append("> 작업 패턴과 습관에서 발견된 인사이트")
        lines.append("")

        # Impact emoji mapping for better readability
        impact_emojis = {
            "positive": "✅",
            "negative": "⚠️",
        }

        # Build table data
        headers = ["영향", "패턴", "제안"]
        rows = []
        for pattern in retro.behavior_patterns:
            impact_emoji = impact_emojis.get(pattern.impact, "ℹ️")
            recommendation = pattern.recommendation if pattern.recommendation else "-"
            rows.append([impact_emoji, pattern.description, recommendation])

        # Render as HTML table
        lines.extend(GameRenderer.render_html_table(
            headers=headers,
            rows=rows,
            title="",
            description="",
            striped=True
        ))

        return lines

    def _build_learning_insights_subsection(self, retro) -> List[str]:
        """Build learning insights subsection of retrospective (HTML version)."""
        lines = []
        if not retro.learning_insights:
            return lines

        lines.append("### 📚 학습 및 성장 분석")
        lines.append("")
        lines.append("> 기술 역량과 학습 궤적을 분석합니다")
        lines.append("")

        # Build table data
        headers = ["분야", "기술", "전문성", "성장 지표"]
        rows = []

        for learning in retro.learning_insights:
            expertise_emoji = {"expert": "👑", "proficient": "⭐", "developing": "🌱", "exploring": "🔍"}.get(
                learning.expertise_level, "📖"
            )
            technologies = ', '.join(learning.technologies)
            technologies = html.escape(technologies, quote=False)
            growth_indicators = '<br>'.join(
                f"• {html.escape(ind, quote=False)}"
                for ind in learning.growth_indicators[:DISPLAY_LIMITS['growth_indicators']]
            ) if learning.growth_indicators else "-"
            expertise_level = html.escape(learning.expertise_level, quote=False)
            domain = html.escape(learning.domain, quote=False)

            rows.append([
                f"{expertise_emoji} {domain}",
                technologies,
                expertise_level,
                growth_indicators
            ])

        # Render as HTML table
        lines.extend(GameRenderer.render_html_table(
            headers=headers,
            rows=rows,
            title="",
            description="",
            striped=True,
            escape_cells=False
        ))

        return lines

    def _build_impact_assessments_subsection(self, retro) -> List[str]:
        """Build impact assessments subsection of retrospective (HTML version)."""
        lines = []
        if not retro.impact_assessments:
            return lines

        lines.append("### 💎 영향도 평가")
        lines.append("")
        lines.append("> 기여의 비즈니스 및 팀 영향을 평가합니다")
        lines.append("")

        # Build table data
        headers = ["카테고리", "기여 횟수", "영향도", "설명"]
        rows = []

        for impact in retro.impact_assessments:
            impact_emoji = {"high": "🔥", "medium": "✨", "low": "💡"}.get(impact.estimated_impact, "📊")
            rows.append([
                f"{impact_emoji} {impact.category}",
                f"{impact.contribution_count:,}건",
                impact.estimated_impact,
                impact.impact_description
            ])

        # Render as HTML table
        lines.extend(GameRenderer.render_html_table(
            headers=headers,
            rows=rows,
            title="",
            description="",
            striped=True
        ))

        return lines

    def _build_collaboration_insights_subsection(self, retro) -> List[str]:
        """Build collaboration insights subsection of retrospective (HTML version)."""
        lines = []
        if not retro.collaboration_insights:
            return lines

        collab = retro.collaboration_insights
        lines.append("### 🤝 협업 심층 분석")
        lines.append("")
        lines.append(f"**협업 강도:** {collab.collaboration_strength}")
        lines.append(f"**협업 품질:** {collab.collaboration_quality}")
        lines.append("")

        if collab.key_partnerships:
            lines.append("**주요 협업 파트너:**")
            lines.append("")

            # Build table data
            headers = ["협업자", "리뷰 횟수", "관계"]
            rows = []
            for person, count, rel_type in collab.key_partnerships:
                rows.append([f"@{person}", f"{count}회", rel_type])

            # Render as HTML table
            lines.extend(GameRenderer.render_html_table(
                headers=headers,
                rows=rows,
                title="",
                description="",
                striped=True
            ))

        if collab.mentorship_indicators:
            lines.append("**멘토링 활동:**")
            for indicator in collab.mentorship_indicators:
                lines.append(f"- {indicator}")
            lines.append("")

        if collab.improvement_areas:
            lines.append("**개선 영역:**")
            for area in collab.improvement_areas:
                lines.append(f"- {area}")
            lines.append("")

        return lines

    def _build_balance_metrics_subsection(self, retro) -> List[str]:
        """Build balance metrics subsection of retrospective (HTML version)."""
        lines = []
        if not retro.balance_metrics:
            return lines

        balance = retro.balance_metrics
        lines.append("### ⚖️ 업무 밸런스 분석")
        lines.append("")

        risk_emoji = {"low": "✅", "moderate": "⚠️", "high": "🚨"}.get(balance.burnout_risk_level, "❓")

        # Main metrics table
        headers = ["지표", "값"]
        rows = [
            ["번아웃 위험도", f"{risk_emoji} {balance.burnout_risk_level}"],
            ["지속가능성 점수", f"{balance.sustainability_score:.0f}/100"],
            ["활동 변동성", f"{balance.activity_variance:.2f}"]
        ]

        lines.extend(GameRenderer.render_html_table(
            headers=headers,
            rows=rows,
            title="",
            description="",
            striped=True
        ))

        if balance.positive_patterns:
            lines.append("**긍정적 패턴:**")
            lines.append("")

            headers = ["패턴"]
            rows = [[f"✅ {pattern}"] for pattern in balance.positive_patterns]

            lines.extend(GameRenderer.render_html_table(
                headers=headers,
                rows=rows,
                title="",
                description="",
                striped=True
            ))

        if balance.burnout_indicators:
            lines.append("**주의 사항:**")
            lines.append("")

            headers = ["지표"]
            rows = [[f"⚠️ {indicator}"] for indicator in balance.burnout_indicators]

            lines.extend(GameRenderer.render_html_table(
                headers=headers,
                rows=rows,
                title="",
                description="",
                striped=True
            ))

        if balance.health_recommendations:
            lines.append("**권장 사항:**")
            lines.append("")

            headers = ["권장사항"]
            rows = [[f"💡 {rec}"] for rec in balance.health_recommendations]

            lines.extend(GameRenderer.render_html_table(
                headers=headers,
                rows=rows,
                title="",
                description="",
                striped=True
            ))

        return lines

    def _build_code_health_subsection(self, retro) -> List[str]:
        """Build code health subsection of retrospective (HTML version)."""
        lines = []
        if not retro.code_health:
            return lines

        health = retro.code_health
        lines.append("### 🏥 코드 건강도 분석")
        lines.append("")

        # Main metrics table
        headers = ["지표", "값"]
        rows = [
            ["유지보수 부담", health.maintenance_burden],
            ["테스트 커버리지 추세", health.test_coverage_trend]
        ]

        lines.extend(GameRenderer.render_html_table(
            headers=headers,
            rows=rows,
            title="",
            description="",
            striped=True
        ))

        if health.code_quality_trends:
            lines.append("**품질 트렌드:**")
            lines.append("")

            headers = ["트렌드"]
            rows = [[trend] for trend in health.code_quality_trends]

            lines.extend(GameRenderer.render_html_table(
                headers=headers,
                rows=rows,
                title="",
                description="",
                striped=True
            ))

        if health.quality_improvement_suggestions:
            lines.append("**개선 제안:**")
            lines.append("")

            headers = ["제안"]
            rows = [[f"💡 {suggestion}"] for suggestion in health.quality_improvement_suggestions]

            lines.extend(GameRenderer.render_html_table(
                headers=headers,
                rows=rows,
                title="",
                description="",
                striped=True
            ))

        return lines

    def _build_actionable_insights_subsection(self, retro) -> List[str]:
        """Build actionable insights subsection of retrospective."""
        lines = []
        if retro.actionable_insights:
            lines.append("### 🎯 실행 가능한 인사이트")
            lines.append("")
            lines.append("> 구체적이고 측정 가능한 개선 방안")
            lines.append("")

            # Group by priority
            high_priority = [ai for ai in retro.actionable_insights if ai.priority == "high"]
            medium_priority = [ai for ai in retro.actionable_insights if ai.priority == "medium"]

            if high_priority:
                lines.append("#### 🔴 높은 우선순위")
                lines.append("")
                for insight in high_priority:
                    lines.append(f"**{insight.title}**")
                    lines.append("")
                    lines.append(f"*{insight.description}*")
                    lines.append("")
                    lines.append(f"**왜 중요한가:** {insight.why_it_matters}")
                    lines.append("")
                    lines.append("**구체적 행동:**")
                    for action in insight.concrete_actions:
                        lines.append(f"1. {action}")
                    lines.append("")
                    lines.append(f"**기대 효과:** {insight.expected_outcome}")
                    lines.append(f"**측정 방법:** {insight.measurement}")
                    lines.append("")
                    lines.append("---")
                    lines.append("")

            if medium_priority:
                lines.append("#### 🟡 중간 우선순위")
                lines.append("")
                for insight in medium_priority[:DISPLAY_LIMITS['medium_priority_insights']]:
                    lines.append(f"**{insight.title}**")
                    lines.append("")
                    lines.append(f"*{insight.description}*")
                    lines.append("")
                    lines.append("**구체적 행동:**")
                    for action in insight.concrete_actions:
                        lines.append(f"- {action}")
                    lines.append("")
            lines.append("")
        return lines

    def _build_areas_for_growth_subsection(self, retro) -> List[str]:
        """Build areas for growth subsection of retrospective (HTML version)."""
        lines = []
        if not retro.areas_for_growth:
            return lines

        lines.append("### 🌱 성장 기회")
        lines.append("")
        lines.append("> 다음 단계로 나아가기 위한 영역")
        lines.append("")

        # Build table data
        headers = ["#", "성장 기회"]
        rows = [[str(i), area] for i, area in enumerate(retro.areas_for_growth, 1)]

        # Render as HTML table
        lines.extend(GameRenderer.render_html_table(
            headers=headers,
            rows=rows,
            title="",
            description="",
            striped=True
        ))

        return lines

    def _build_narrative_subsection(self, retro) -> List[str]:
        """Build narrative subsection of retrospective."""
        lines = []
        if retro.retrospective_narrative:
            lines.append("### 📖 회고 스토리")
            lines.append("")
            lines.append("> 당신의 여정을 이야기로 풀어냅니다")
            lines.append("")
            for paragraph in retro.retrospective_narrative:
                lines.append(paragraph)
                lines.append("")
        return lines
