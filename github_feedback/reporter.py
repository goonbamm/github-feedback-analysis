"""Report generation for GitHub feedback analysis."""

from __future__ import annotations

from dataclasses import dataclass
from html import escape
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple

from .console import Console
from .constants import AWARD_CATEGORIES, AWARD_KEYWORDS, COLLECTION_LIMITS, DISPLAY_LIMITS
from .models import MetricSnapshot, PromptRequest

console = Console()


def _format_metric_value(value: object) -> str:
    """Format numeric values with separators while keeping strings intact."""

    if isinstance(value, bool):
        return str(value)
    if isinstance(value, int):
        return f"{value:,}"
    if isinstance(value, float):
        return f"{value:,.2f}"
    return str(value)


@dataclass(slots=True)
class Reporter:
    """Create human-readable artefacts from metrics."""

    output_dir: Path = Path("reports")

    def ensure_structure(self) -> None:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        (self.output_dir / "charts").mkdir(parents=True, exist_ok=True)

    def _categorize_awards(self, awards: List[str]) -> dict:
        """Categorize awards by type for better organization."""
        # Initialize categories from constants
        categories = {label: [] for label in AWARD_CATEGORIES.values()}

        for award in awards:
            categorized = False
            # Check each category's keywords
            for category_key, keywords in AWARD_KEYWORDS.items():
                if any(keyword in award for keyword in keywords):
                    category_label = AWARD_CATEGORIES[category_key]
                    categories[category_label].append(award)
                    categorized = True
                    break

            # Default category if no keywords match
            if not categorized:
                categories[AWARD_CATEGORIES['basic']].append(award)

        # Remove empty categories
        return {k: v for k, v in categories.items() if v}


    def _build_prompt_context(self, metrics: MetricSnapshot) -> str:
        """Create a reusable context block describing the metrics."""

        lines: List[str] = []
        period_label = (
            f"지난 {metrics.months}개월"
            if metrics.months and metrics.months < 12
            else "올해"
        )

        lines.append(f"Repository: {metrics.repo}")
        lines.append(f"Period: {period_label}")
        lines.append("")

        if metrics.summary:
            lines.append("Summary:")
            for key, value in metrics.summary.items():
                lines.append(f"- {key.title()}: {value}")
            lines.append("")

        if metrics.stats:
            lines.append("Metrics:")
            for domain, domain_stats in metrics.stats.items():
                lines.append(f"- {domain.title()}:")
                for stat_name, stat_value in domain_stats.items():
                    lines.append(
                        "  • {}: {}".format(
                            stat_name.replace("_", " ").title(),
                            _format_metric_value(stat_value)
                            if isinstance(stat_value, (int, float))
                            else stat_value,
                        )
                    )
            lines.append("")

        if metrics.highlights:
            lines.append("Growth Highlights:")
            for highlight in metrics.highlights:
                lines.append(f"- {highlight}")
            lines.append("")

        if metrics.spotlight_examples:
            lines.append("Spotlight Examples:")
            for category, entries in metrics.spotlight_examples.items():
                lines.append(f"- {category.replace('_', ' ').title()}")
                for entry in entries:
                    lines.append(f"  • {entry}")
            lines.append("")

        if metrics.yearbook_story:
            lines.append("Year In Review:")
            for paragraph in metrics.yearbook_story:
                lines.append(f"- {paragraph}")
            lines.append("")

        if metrics.awards:
            lines.append("Awards:")
            for award in metrics.awards:
                lines.append(f"- {award}")
            lines.append("")

        if metrics.evidence:
            lines.append("Evidence Links:")
            for domain, links in metrics.evidence.items():
                for link in links:
                    lines.append(f"- {domain.title()}: {link}")

        return "\n".join(lines).strip()

    def _build_header_and_summary(self, metrics: MetricSnapshot) -> List[str]:
        """Build header and summary section."""
        lines = ["# 🚀 GitHub Feedback Report", ""]
        lines.append(f"**Repository**: {metrics.repo}")
        lines.append(f"**Period**: {metrics.months} months")

        if metrics.since_date and metrics.until_date:
            since_str = metrics.since_date.strftime("%Y-%m-%d")
            until_str = metrics.until_date.strftime("%Y-%m-%d")
            lines.append(f"**Analysis Period**: {since_str} ~ {until_str}")

        lines.append("")
        lines.append("---")
        lines.append("")

        return lines

    def _build_table_of_contents(self, metrics: MetricSnapshot) -> List[str]:
        """Build table of contents section."""
        lines = ["## 📑 목차", ""]

        sections = [
            ("📊 Executive Summary", "한눈에 보는 핵심 지표"),
            ("🏆 Awards Cabinet", "획득한 어워드"),
            ("✨ Growth Highlights", "성장 하이라이트"),
            ("📈 Monthly Trends", "월별 활동 트렌드"),
        ]

        if metrics.detailed_feedback:
            sections.append(("💡 Detailed Feedback", "상세 피드백"))

        # Add retrospective section
        if metrics.retrospective:
            sections.append(("🔍 Deep Retrospective", "심층 회고 분석"))

        sections.extend([
            ("🎯 Spotlight Examples", "주요 기여 사례"),
            ("💻 Tech Stack", "기술 스택 분석"),
            ("🤝 Collaboration", "협업 네트워크"),
            ("🤔 Reflection", "회고 질문"),
            ("📊 Detailed Metrics", "상세 메트릭"),
            ("🔗 Evidence", "증거 링크"),
        ])

        for i, (title, desc) in enumerate(sections, 1):
            lines.append(f"{i}. **{title}** - {desc}")

        lines.append("")
        lines.append("---")
        lines.append("")
        return lines

    def _build_executive_summary(self, metrics: MetricSnapshot) -> List[str]:
        """Build executive summary section with key highlights."""
        lines = ["## 📊 Executive Summary", ""]
        lines.append("> 활동 기간의 핵심 성과를 한눈에 확인하세요")
        lines.append("")

        # Key metrics in a box format
        total_activity = sum([
            metrics.stats.get("commits", {}).get("total", 0),
            metrics.stats.get("pull_requests", {}).get("total", 0),
            metrics.stats.get("reviews", {}).get("total", 0),
        ])

        lines.append("### 📈 핵심 지표")
        lines.append("")
        lines.append("| 지표 | 값 | 설명 |")
        lines.append("|------|-----|------|")

        for key, value in metrics.summary.items():
            display_value = (
                _format_metric_value(value) if isinstance(value, (int, float)) else str(value)
            )
            # Add descriptions for each metric
            descriptions = {
                "velocity": "월평균 커밋 속도",
                "collaboration": "월평균 협업 활동",
                "stability": "안정성 점수",
                "growth": "전체 성장 요약"
            }
            desc = descriptions.get(key, "")
            lines.append(f"| **{key.title()}** | {display_value} | {desc} |")

        lines.append("")

        # Quick stats
        if metrics.awards:
            lines.append(f"🏆 **총 {len(metrics.awards)}개의 어워드 획득**")

        if metrics.highlights:
            lines.append(f"✨ **{len(metrics.highlights)}개의 주요 성과**")

        lines.append("")
        lines.append("---")
        lines.append("")

        return lines

    def _build_metrics_section(self, metrics: MetricSnapshot) -> List[str]:
        """Build metrics section."""
        lines = ["## 📊 Detailed Metrics", ""]
        lines.append("> 각 활동 영역별 상세 수치를 확인하세요")
        lines.append("")

        for domain, domain_stats in metrics.stats.items():
            lines.append(f"### {domain.title()}")
            for stat_name, stat_value in domain_stats.items():
                formatted_value = (
                    _format_metric_value(stat_value)
                    if isinstance(stat_value, (int, float))
                    else str(stat_value)
                )
                lines.append(f"- **{stat_name.replace('_', ' ').title()}**: {formatted_value}")
            lines.append("")
        return lines

    def _build_highlights_section(self, metrics: MetricSnapshot) -> List[str]:
        """Build growth highlights section."""
        if not metrics.highlights:
            return []

        lines = ["## ✨ Growth Highlights", ""]
        lines.append("> 이번 기간 동안의 주요 성과와 성장 포인트")
        lines.append("")
        for i, highlight in enumerate(metrics.highlights, 1):
            lines.append(f"{i}. {highlight}")
        lines.append("")
        lines.append("---")
        lines.append("")
        return lines

    def _build_spotlight_section(self, metrics: MetricSnapshot) -> List[str]:
        """Build spotlight examples section."""
        if not metrics.spotlight_examples:
            return []

        lines = ["## 🎯 Spotlight Examples", ""]
        lines.append("> 주목할 만한 기여 사례")
        lines.append("")
        for category, entries in metrics.spotlight_examples.items():
            lines.append(f"### {category.replace('_', ' ').title()}")
            for entry in entries:
                lines.append(f"- {entry}")
            lines.append("")
        lines.append("---")
        lines.append("")
        return lines

    def _build_year_in_review_section(self, metrics: MetricSnapshot) -> List[str]:
        """Build comprehensive year in review section combining story and detailed review."""
        if not metrics.yearbook_story and not metrics.year_end_review:
            return []

        lines = ["## 📅 Year in Review", ""]
        lines.append("> 한 해의 여정을 돌아봅니다")
        lines.append("")

        # Story beats
        if metrics.yearbook_story:
            lines.append("### 🌟 올해의 이야기")
            lines.append("")
            for paragraph in metrics.yearbook_story:
                lines.append(paragraph)
                lines.append("")

        # Year end review details
        if metrics.year_end_review:
            if metrics.year_end_review.proudest_moments:
                lines.append("### 🏅 자랑스러운 순간들")
                lines.append("")
                for moment in metrics.year_end_review.proudest_moments:
                    lines.append(f"- {moment}")
                lines.append("")

            if metrics.year_end_review.biggest_challenges:
                lines.append("### 💪 극복한 도전들")
                lines.append("")
                for challenge in metrics.year_end_review.biggest_challenges:
                    lines.append(f"- {challenge}")
                lines.append("")

            if metrics.year_end_review.lessons_learned:
                lines.append("### 📚 배운 교훈들")
                lines.append("")
                for lesson in metrics.year_end_review.lessons_learned:
                    lines.append(f"- {lesson}")
                lines.append("")

            if metrics.year_end_review.next_year_goals:
                lines.append("### 🎯 내년 목표")
                lines.append("")
                for goal in metrics.year_end_review.next_year_goals:
                    lines.append(f"- {goal}")
                lines.append("")

        lines.append("---")
        lines.append("")
        return lines

    def _build_awards_section(self, metrics: MetricSnapshot) -> List[str]:
        """Build awards cabinet section."""
        if not metrics.awards:
            return []

        lines = ["## 🏆 Awards Cabinet", ""]
        lines.append(f"**총 {len(metrics.awards)}개의 어워드를 획득했습니다!**")
        lines.append("")

        categories = self._categorize_awards(metrics.awards)
        for category_name, category_awards in categories.items():
            if category_awards:
                lines.append(f"### {category_name}")
                for award in category_awards:
                    lines.append(f"- {award}")
                lines.append("")
        return lines


    def _build_detailed_feedback_section(self, metrics: MetricSnapshot) -> List[str]:
        """Build detailed feedback section."""
        if not metrics.detailed_feedback:
            return []

        lines = ["## 💡 Detailed Feedback", ""]
        lines.append("> 코드, PR, 리뷰, 이슈 품질에 대한 상세 분석")
        lines.append("")
        feedback = metrics.detailed_feedback

        # Commit message feedback
        if feedback.commit_feedback:
            lines.extend(self._build_commit_feedback(feedback.commit_feedback))

        # PR title feedback
        if feedback.pr_title_feedback:
            lines.extend(self._build_pr_title_feedback(feedback.pr_title_feedback))

        # Review tone feedback
        if feedback.review_tone_feedback:
            lines.extend(self._build_review_tone_feedback(feedback.review_tone_feedback))

        # Issue feedback
        if feedback.issue_feedback:
            lines.extend(self._build_issue_feedback(feedback.issue_feedback))

        lines.append("---")
        lines.append("")
        return lines

    def _build_feedback_section(
        self,
        title: str,
        feedback_data: Any,
        stats_config: Dict[str, str],
        example_formatter: Optional[Callable[[Any], str]] = None,
        examples_poor_attr: str = "examples_poor"
    ) -> List[str]:
        """Build a feedback subsection with a common structure.

        Args:
            title: Section title (e.g., "### 📝 커밋 메시지 품질")
            feedback_data: Feedback data object with stats and examples
            stats_config: Dictionary mapping stat names to labels
                - 'total': tuple of (attribute_name, label, unit)
                - 'good': tuple of (attribute_name, label, unit)
                - 'poor': tuple of (attribute_name, label, unit)
                - additional stats as needed
            example_formatter: Optional function to format examples
            examples_poor_attr: Attribute name for poor examples (default: "examples_poor")

        Returns:
            List of markdown lines
        """
        lines = [title, ""]

        # Build summary statistics
        total_attr, total_label, unit = stats_config.get('total', (None, None, '개'))
        good_attr, good_label, _ = stats_config.get('good', (None, None, '개'))
        poor_attr, poor_label, _ = stats_config.get('poor', (None, None, '개'))

        total_value = getattr(feedback_data, total_attr, 0) if total_attr else 0
        good_value = getattr(feedback_data, good_attr, 0) if good_attr else 0
        poor_value = getattr(feedback_data, poor_attr, 0) if poor_attr else 0

        if total_value > 0:
            good_pct = (good_value / total_value) * 100
            lines.append(f"**{total_label}**: {total_value}{unit}")
            lines.append(f"**{good_label}**: {good_value}{unit} ({good_pct:.1f}%)")
            lines.append(f"**{poor_label}**: {poor_value}{unit}")

            # Add additional stats if configured
            for key, (attr, label, stat_unit) in stats_config.items():
                if key not in ('total', 'good', 'poor'):
                    value = getattr(feedback_data, attr, 0)
                    lines.append(f"**{label}**: {value}{stat_unit}")
        else:
            lines.append(f"- {total_label}: {total_value}")
            lines.append(f"- {good_label}: {good_value}")
            lines.append(f"- {poor_label}: {poor_value}")

            # Add additional stats if configured
            for key, (attr, label, stat_unit) in stats_config.items():
                if key not in ('total', 'good', 'poor'):
                    value = getattr(feedback_data, attr, 0)
                    lines.append(f"- {label}: {value}")
        lines.append("")

        # Suggestions section
        if hasattr(feedback_data, 'suggestions') and feedback_data.suggestions:
            lines.append("#### 💡 개선 제안")
            lines.append("")
            for i, suggestion in enumerate(feedback_data.suggestions, 1):
                lines.append(f"{i}. {suggestion}")
            lines.append("")

        # Good examples section
        if hasattr(feedback_data, 'examples_good') and feedback_data.examples_good:
            lines.append("#### ✅ 좋은 예시")
            lines.append("")
            for example in feedback_data.examples_good[:DISPLAY_LIMITS['feedback_examples']]:
                if example_formatter:
                    lines.append(f"- {example_formatter(example)}")
                elif isinstance(example, dict):
                    lines.append(f"- {example}")
                else:
                    lines.append(f"- {example}")
            lines.append("")

        # Poor/improve examples section
        poor_examples = getattr(feedback_data, examples_poor_attr, None)
        if poor_examples:
            lines.append("#### ⚠️ 개선이 필요한 예시")
            lines.append("")
            for example in poor_examples[:DISPLAY_LIMITS['feedback_examples']]:
                if example_formatter:
                    lines.append(f"- {example_formatter(example)}")
                elif isinstance(example, dict):
                    lines.append(f"- {example}")
                else:
                    lines.append(f"- {example}")
            lines.append("")

        return lines

    def _build_commit_feedback(self, cf) -> List[str]:
        """Build commit feedback subsection."""
        def format_commit_example(example):
            if isinstance(example, dict):
                return f"`{example.get('message', '')}` ({example.get('sha', '')[:7]})"
            return str(example)

        return self._build_feedback_section(
            title="### 📝 커밋 메시지 품질",
            feedback_data=cf,
            stats_config={
                'total': ('total_commits', '총 커밋', '개'),
                'good': ('good_messages', '좋은 메시지', '개'),
                'poor': ('poor_messages', '개선 필요', '개'),
            },
            example_formatter=format_commit_example,
        )

    def _build_pr_title_feedback(self, pf) -> List[str]:
        """Build PR title feedback subsection."""
        def format_pr_example(example):
            if isinstance(example, dict):
                return f"#{example.get('number', '')}: `{example.get('title', '')}`"
            return str(example)

        return self._build_feedback_section(
            title="### 🔀 PR 제목 품질",
            feedback_data=pf,
            stats_config={
                'total': ('total_prs', '총 PR', '개'),
                'good': ('clear_titles', '명확한 제목', '개'),
                'poor': ('vague_titles', '모호한 제목', '개'),
            },
            example_formatter=format_pr_example,
        )

    def _build_review_tone_feedback(self, rf) -> List[str]:
        """Build review tone feedback subsection."""
        return self._build_feedback_section(
            title="### 👀 리뷰 톤 분석",
            feedback_data=rf,
            stats_config={
                'total': ('total_reviews', '총 리뷰', '개'),
                'good': ('constructive_reviews', '건설적인 리뷰', '개'),
                'poor': ('harsh_reviews', '가혹한 리뷰', '개'),
                'neutral': ('neutral_reviews', '중립적인 리뷰', '개'),
            },
            examples_poor_attr='examples_improve',
        )

    def _build_issue_feedback(self, isf) -> List[str]:
        """Build issue feedback subsection."""
        def format_issue_example(example):
            if isinstance(example, dict):
                return f"#{example.get('number', '')}: `{example.get('title', '')}`"
            return str(example)

        return self._build_feedback_section(
            title="### 🐛 이슈 품질",
            feedback_data=isf,
            stats_config={
                'total': ('total_issues', '총 이슈', '개'),
                'good': ('well_described', '잘 작성됨', '개'),
                'poor': ('poorly_described', '개선 필요', '개'),
            },
            example_formatter=format_issue_example,
        )

    def _build_monthly_trends_section(self, metrics: MetricSnapshot) -> List[str]:
        """Build monthly trends section."""
        if not metrics.monthly_trends:
            return []

        lines = ["## 📈 Monthly Trends", ""]
        lines.append("> 월별 활동 패턴과 트렌드 분석")
        lines.append("")

        if metrics.monthly_insights and metrics.monthly_insights.insights:
            lines.append("### 💡 인사이트")
            lines.append("")
            for i, insight in enumerate(metrics.monthly_insights.insights, 1):
                lines.append(f"{i}. {insight}")
            lines.append("")

        lines.append("### 📊 월별 상세 데이터")
        lines.append("")
        lines.append("| 월 | 커밋 | PR | 리뷰 | 이슈 | 총 활동 |")
        lines.append("|---|---|---|---|---|---|")
        for trend in metrics.monthly_trends:
            total_activity = trend.commits + trend.pull_requests + trend.reviews + trend.issues
            lines.append(
                f"| {trend.month} | {trend.commits} | {trend.pull_requests} | "
                f"{trend.reviews} | {trend.issues} | **{total_activity}** |"
            )
        lines.append("")
        lines.append("---")
        lines.append("")
        return lines

    def _build_tech_stack_section(self, metrics: MetricSnapshot) -> List[str]:
        """Build tech stack section."""
        if not metrics.tech_stack:
            return []

        lines = ["## 💻 Tech Stack Analysis", ""]
        lines.append("> 사용한 기술과 언어 분포")
        lines.append("")
        lines.append(f"**다양성 점수**: {metrics.tech_stack.diversity_score:.2f} (0-1 척도)")
        lines.append("")
        lines.append("**주요 사용 언어:**")
        lines.append("")
        for i, lang in enumerate(metrics.tech_stack.top_languages[:5], 1):
            count = metrics.tech_stack.languages.get(lang, 0)
            lines.append(f"{i}. **{lang}** - {count}개 파일")
        lines.append("")
        lines.append("---")
        lines.append("")
        return lines

    def _build_collaboration_section(self, metrics: MetricSnapshot) -> List[str]:
        """Build collaboration section."""
        if not metrics.collaboration:
            return []

        lines = ["## 🤝 Collaboration Network", ""]
        lines.append("> 함께 성장한 동료들과의 협업")
        lines.append("")
        lines.append(f"- 받은 리뷰 수: **{metrics.collaboration.review_received_count}건**")
        lines.append(f"- 협업한 사람 수: **{metrics.collaboration.unique_collaborators}명**")
        lines.append("")

        if metrics.collaboration.top_reviewers:
            lines.append("### 🌟 주요 리뷰어")
            lines.append("")
            for i, reviewer in enumerate(metrics.collaboration.top_reviewers, 1):
                count = metrics.collaboration.pr_reviewers.get(reviewer, 0)
                lines.append(f"{i}. **@{reviewer}** - {count}회 리뷰")
            lines.append("")
        lines.append("---")
        lines.append("")
        return lines

    def _build_reflection_prompts_section(self, metrics: MetricSnapshot) -> List[str]:
        """Build reflection prompts section."""
        if not (metrics.reflection_prompts and metrics.reflection_prompts.questions):
            return []

        lines = ["## 🤔 Reflection Prompts", ""]
        lines.append("> 스스로에게 물어보세요")
        lines.append("")
        for i, question in enumerate(metrics.reflection_prompts.questions, 1):
            lines.append(f"{i}. {question}")
        lines.append("")
        lines.append("---")
        lines.append("")
        return lines

    def _build_evidence_section_improved(self, metrics: MetricSnapshot) -> List[str]:
        """Build evidence section."""
        if not metrics.evidence:
            return []

        lines = ["## 🔗 Evidence Links", ""]
        lines.append("> 상세 데이터를 확인할 수 있는 링크")
        lines.append("")
        for domain, links in metrics.evidence.items():
            lines.append(f"### {domain.title()}")
            for link in links:
                lines.append(f"- [{domain.title()} 보기]({link})")
            lines.append("")
        lines.append("---")
        lines.append("")
        return lines

    def _build_retrospective_section(self, metrics: MetricSnapshot) -> List[str]:
        """Build comprehensive retrospective analysis section."""
        if not metrics.retrospective:
            return []

        retro = metrics.retrospective
        lines = ["## 🔍 Deep Retrospective Analysis", ""]
        lines.append("> 데이터 기반의 심층적인 회고와 인사이트")
        lines.append("")

        # Executive Summary
        if retro.executive_summary:
            lines.append("### 📋 회고 요약")
            lines.append("")
            lines.append(retro.executive_summary)
            lines.append("")

        # Key Wins
        if retro.key_wins:
            lines.append("### 🎉 주요 성과")
            lines.append("")
            lines.append("> 이번 기간 동안 달성한 핵심 성과들입니다")
            lines.append("")
            for i, win in enumerate(retro.key_wins, 1):
                lines.append(f"{i}. **{win}**")
            lines.append("")

        # Time Comparisons
        if retro.time_comparisons:
            lines.append("### 📊 기간 비교 분석")
            lines.append("")
            lines.append("> 전반기와 후반기의 변화 추이를 비교합니다")
            lines.append("")
            lines.append("| 지표 | 전반기 | 후반기 | 변화량 | 변화율 | 의미 |")
            lines.append("|------|--------|--------|--------|--------|------|")

            for tc in retro.time_comparisons:
                direction_emoji = "📈" if tc.direction == "increasing" else "📉" if tc.direction == "decreasing" else "➡️"
                significance_text = {
                    "major": "큰 변화",
                    "moderate": "중간 변화",
                    "minor": "작은 변화"
                }.get(tc.significance, tc.significance)

                lines.append(
                    f"| {tc.metric_name} | {tc.previous_value:.1f} | {tc.current_value:.1f} | "
                    f"{tc.change_absolute:+.1f} | {tc.change_percentage:+.1f}% | "
                    f"{direction_emoji} {significance_text} |"
                )
            lines.append("")

        # Behavior Patterns
        if retro.behavior_patterns:
            lines.append("### 🧠 행동 패턴 분석")
            lines.append("")
            lines.append("> 작업 패턴과 습관에서 발견된 인사이트")
            lines.append("")

            for pattern in retro.behavior_patterns:
                impact_emoji = "✅" if pattern.impact == "positive" else "⚠️" if pattern.impact == "negative" else "ℹ️"
                lines.append(f"#### {impact_emoji} {pattern.description}")
                lines.append("")

                if pattern.evidence:
                    lines.append("**근거:**")
                    for evidence in pattern.evidence:
                        lines.append(f"- {evidence}")
                    lines.append("")

                if pattern.recommendation:
                    lines.append(f"**제안:** {pattern.recommendation}")
                    lines.append("")
            lines.append("")

        # Learning Insights
        if retro.learning_insights:
            lines.append("### 📚 학습 및 성장 분석")
            lines.append("")
            lines.append("> 기술 역량과 학습 궤적을 분석합니다")
            lines.append("")

            for learning in retro.learning_insights:
                expertise_emoji = {"expert": "👑", "proficient": "⭐", "developing": "🌱", "exploring": "🔍"}.get(
                    learning.expertise_level, "📖"
                )
                lines.append(f"#### {expertise_emoji} {learning.domain}")
                lines.append("")
                lines.append(f"**기술:** {', '.join(learning.technologies)}")
                lines.append(f"**전문성 수준:** {learning.expertise_level}")
                lines.append("")

                if learning.growth_indicators:
                    lines.append("**성장 지표:**")
                    for indicator in learning.growth_indicators:
                        lines.append(f"- {indicator}")
                    lines.append("")
            lines.append("")

        # Impact Assessments
        if retro.impact_assessments:
            lines.append("### 💎 영향도 평가")
            lines.append("")
            lines.append("> 기여의 비즈니스 및 팀 영향을 평가합니다")
            lines.append("")

            for impact in retro.impact_assessments:
                impact_emoji = {"high": "🔥", "medium": "✨", "low": "💡"}.get(impact.estimated_impact, "📊")
                lines.append(f"#### {impact_emoji} {impact.category}")
                lines.append("")
                lines.append(f"**기여 횟수:** {impact.contribution_count:,}건")
                lines.append(f"**영향도:** {impact.estimated_impact}")
                lines.append(f"**설명:** {impact.impact_description}")
                lines.append("")

                if impact.key_achievements:
                    lines.append("**핵심 성과:**")
                    for achievement in impact.key_achievements:
                        lines.append(f"- {achievement}")
                    lines.append("")
            lines.append("")

        # Collaboration Insights
        if retro.collaboration_insights:
            collab = retro.collaboration_insights
            lines.append("### 🤝 협업 심층 분석")
            lines.append("")
            lines.append(f"**협업 강도:** {collab.collaboration_strength}")
            lines.append(f"**협업 품질:** {collab.collaboration_quality}")
            lines.append("")

            if collab.key_partnerships:
                lines.append("**주요 협업 파트너:**")
                lines.append("")
                lines.append("| 협업자 | 리뷰 횟수 | 관계 |")
                lines.append("|--------|-----------|------|")
                for person, count, rel_type in collab.key_partnerships:
                    lines.append(f"| @{person} | {count}회 | {rel_type} |")
                lines.append("")

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
            lines.append("")

        # Balance Metrics
        if retro.balance_metrics:
            balance = retro.balance_metrics
            lines.append("### ⚖️ 업무 밸런스 분석")
            lines.append("")

            risk_emoji = {"low": "✅", "moderate": "⚠️", "high": "🚨"}.get(balance.burnout_risk_level, "❓")
            lines.append(f"**번아웃 위험도:** {risk_emoji} {balance.burnout_risk_level}")
            lines.append(f"**지속가능성 점수:** {balance.sustainability_score:.0f}/100")
            lines.append(f"**활동 변동성:** {balance.activity_variance:.2f}")
            lines.append("")

            if balance.positive_patterns:
                lines.append("**긍정적 패턴:**")
                for pattern in balance.positive_patterns:
                    lines.append(f"- ✅ {pattern}")
                lines.append("")

            if balance.burnout_indicators:
                lines.append("**주의 사항:**")
                for indicator in balance.burnout_indicators:
                    lines.append(f"- ⚠️ {indicator}")
                lines.append("")

            if balance.health_recommendations:
                lines.append("**권장 사항:**")
                for rec in balance.health_recommendations:
                    lines.append(f"- 💡 {rec}")
                lines.append("")
            lines.append("")

        # Code Health
        if retro.code_health:
            health = retro.code_health
            lines.append("### 🏥 코드 건강도 분석")
            lines.append("")
            lines.append(f"**유지보수 부담:** {health.maintenance_burden}")
            lines.append(f"**테스트 커버리지 추세:** {health.test_coverage_trend}")
            lines.append("")

            if health.code_quality_trends:
                lines.append("**품질 트렌드:**")
                for trend in health.code_quality_trends:
                    lines.append(f"- {trend}")
                lines.append("")

            if health.quality_improvement_suggestions:
                lines.append("**개선 제안:**")
                for suggestion in health.quality_improvement_suggestions:
                    lines.append(f"- 💡 {suggestion}")
                lines.append("")
            lines.append("")

        # Actionable Insights
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
                for insight in medium_priority[:DISPLAY_LIMITS['medium_priority_insights']]:  # Limit to top N for readability
                    lines.append(f"**{insight.title}**")
                    lines.append("")
                    lines.append(f"*{insight.description}*")
                    lines.append("")
                    lines.append("**구체적 행동:**")
                    for action in insight.concrete_actions:
                        lines.append(f"- {action}")
                    lines.append("")
            lines.append("")

        # Areas for Growth
        if retro.areas_for_growth:
            lines.append("### 🌱 성장 기회")
            lines.append("")
            lines.append("> 다음 단계로 나아가기 위한 영역")
            lines.append("")
            for i, area in enumerate(retro.areas_for_growth, 1):
                lines.append(f"{i}. {area}")
            lines.append("")

        # Narrative
        if retro.retrospective_narrative:
            lines.append("### 📖 회고 스토리")
            lines.append("")
            lines.append("> 당신의 여정을 이야기로 풀어냅니다")
            lines.append("")
            for paragraph in retro.retrospective_narrative:
                lines.append(paragraph)
                lines.append("")

        lines.append("---")
        lines.append("")
        return lines

    def generate_markdown(self, metrics: MetricSnapshot) -> Path:
        """Create a markdown report for the provided metrics.

        Improved report structure for better user experience:
        1. Header with basic info
        2. Table of Contents for easy navigation
        3. Executive Summary for quick overview
        4. Awards Cabinet to celebrate achievements
        5. Growth Highlights to show progress
        6. Monthly Trends for pattern analysis
        7. Detailed Feedback for actionable insights
        8. Spotlight Examples for concrete evidence
        9. Tech Stack to show technical breadth
        10. Collaboration Network to show teamwork
        11. Year in Review for storytelling
        12. Reflection Prompts for introspection
        13. Detailed Metrics for deep dive
        14. Evidence Links for verification
        """
        self.ensure_structure()
        report_path = self.output_dir / "report.md"

        console.log("Writing markdown report", f"path={report_path}")

        # Build all sections in improved order
        sections = [
            # 1. Header with basic info
            self._build_header_and_summary(metrics),
            # 2. Table of Contents
            self._build_table_of_contents(metrics),
            # 3. Executive Summary - Quick overview
            self._build_executive_summary(metrics),
            # 4. Awards Cabinet - Celebrate achievements first!
            self._build_awards_section(metrics),
            # 5. Growth Highlights - Show the story
            self._build_highlights_section(metrics),
            # 6. Monthly Trends - Show patterns
            self._build_monthly_trends_section(metrics),
            # 7. Detailed Feedback - Actionable insights
            self._build_detailed_feedback_section(metrics),
            # 8. Deep Retrospective - Comprehensive analysis NEW!
            self._build_retrospective_section(metrics),
            # 9. Spotlight Examples - Concrete evidence
            self._build_spotlight_section(metrics),
            # 10. Tech Stack - Technical breadth
            self._build_tech_stack_section(metrics),
            # 11. Collaboration - Teamwork
            self._build_collaboration_section(metrics),
            # 12. Year in Review - Complete story (merged with year-end review)
            self._build_year_in_review_section(metrics),
            # 13. Reflection Prompts - Think deeper
            self._build_reflection_prompts_section(metrics),
            # 14. Detailed Metrics - For those who want numbers
            self._build_metrics_section(metrics),
            # 15. Evidence Links - Verification
            self._build_evidence_section_improved(metrics),
        ]

        # Combine all sections
        all_lines = []
        for section in sections:
            all_lines.extend(section)

        report_path.write_text("\n".join(all_lines), encoding="utf-8")
        return report_path

    # ------------------------------------------------------------------
    # Rich visual reporting
    # ------------------------------------------------------------------

    def generate_prompt_packets(
        self, metrics: MetricSnapshot
    ) -> List[Tuple[PromptRequest, Path]]:
        """Create multi-angle LLM prompts for annual feedback synthesis."""

        self.ensure_structure()
        prompts_dir = self.output_dir / "prompts"
        prompts_dir.mkdir(parents=True, exist_ok=True)

        context = self._build_prompt_context(metrics)
        if context:
            context_block = context
        else:
            context_block = (
                f"Repository: {metrics.repo}\nPeriod: 지난 {metrics.months}개월"
            )

        definitions: List[Tuple[str, str, str]] = [
            (
                "strengths_overview",
                "연간 활동 총평 (장점 중심)",
                (
                    "아래는 최근 활동 요약입니다. 위 데이터를 바탕으로 팀/조직 관점에서 바라본 "
                    "성과의 장점 5가지를 bullet로 정리해 주세요. 각 bullet에는 (1) 어떤 활동이나 "
                    "지표가 근거인지, (2) 조직에 준 영향이 무엇인지 포함해 주세요."
                ),
            ),
            (
                "collaboration_improvements",
                "협업 및 리뷰 문화 보완점",
                (
                    "Collaborations 관련 수치와 Spotlight Examples, Year in Review 내용을 참고하여 "
                    "리뷰 문화/협업 측면에서 개선이 필요한 점 5가지를 제안해 주세요. 각 항목에는 "
                    "(1) 현재 활동 패턴, (2) 위험 또는 기회, (3) 다음 분기 액션 아이디어를 포함해 주세요."
                ),
            ),
            (
                "quality_balance",
                "코드 품질 및 안정성 평가",
                (
                    "Stability 관련 요약, Issues 통계, Spotlight 사례를 근거로 코드 품질과 안정성 유지 "
                    "측면의 장점과 보완점을 각각 3개씩 작성해 주세요. 가능하다면 Spotlight PR의 구체적 "
                    "예시를 인용해 주세요."
                ),
            ),
            (
                "growth_story",
                "연간 성장 스토리와 핵심 기여",
                (
                    "Year in Review, Growth Highlights, Awards 정보를 기반으로 세 단락으로 구성된 서사를 작성해 주세요. "
                    "1단락: 올해 어떤 역량이 가장 성장했는지, 2단락: 저장소에 어떤 영역에 중점적으로 기여했는지, "
                    "3단락: 그 결과 팀이나 비즈니스에 기대되는 파급효과가 무엇인지 설명해 주세요."
                ),
            ),
            (
                "next_half_goals",
                "차기 목표 및 실행 계획",
                (
                    "Summary와 위에서 도출한 개선점들을 참고하여 다음 기간(6개월)을 위한 상위 3개 목표와 "
                    "각 목표별 실행 계획을 작성해 주세요. 실행 계획에는 측정 가능한 지표를 포함해 주세요."
                ),
            ),
        ]

        generated: List[Tuple[PromptRequest, Path]] = []
        for identifier, title, instructions in definitions:
            prompt_text = f"{instructions}\n\n{context_block}".strip()
            request = PromptRequest(
                identifier=identifier,
                title=title,
                instructions=instructions,
                prompt=prompt_text,
            )

            prompt_path = prompts_dir / f"{identifier}.txt"
            prompt_lines = [
                f"# {title}",
                "",
                "## Instructions",
                instructions,
                "",
                "## Context",
                context_block,
                "",
                "## Prompt (ready to send)",
                prompt_text,
                "",
            ]
            prompt_path.write_text("\n".join(prompt_lines), encoding="utf-8")
            generated.append((request, prompt_path))

        return generated

    def _create_charts(self, metrics: MetricSnapshot) -> List[Tuple[str, Path]]:
        """Render SVG bar charts for numeric metric domains."""

        charts_dir = self.output_dir / "charts"
        created: List[Tuple[str, Path]] = []

        for domain, domain_stats in metrics.stats.items():
            numeric_stats: List[Tuple[str, float, object]] = []
            for stat_name, stat_value in domain_stats.items():
                if isinstance(stat_value, (int, float)):
                    numeric_stats.append((stat_name, float(stat_value), stat_value))

            if not numeric_stats:
                continue

            values = [value for _, value, _ in numeric_stats]
            max_value = max(values) if values else 1.0
            safe_domain = domain.lower().replace(" ", "_")
            chart_path = charts_dir / f"{safe_domain}.svg"

            width = 720
            chart_width = 520
            bar_height = 28
            spacing = 18
            top_padding = 48
            left_padding = 160
            height = top_padding + spacing + (bar_height + spacing) * len(values)

            svg_parts = [
                f"<svg xmlns='http://www.w3.org/2000/svg' width='{width}' height='{height}' viewBox='0 0 {width} {height}'>",
                "<defs>",
                "<linearGradient id='barGradient' x1='0%' x2='100%' y1='0%' y2='0%'>",
                "<stop offset='0%' stop-color='#60a5fa' />",
                "<stop offset='100%' stop-color='#2563eb' />",
                "</linearGradient>",
                "</defs>",
                "<rect width='100%' height='100%' fill='rgba(15,23,42,0.75)' rx='24' />",
                f"<text x='{width/2}' y='32' text-anchor='middle' fill='#38bdf8' font-size='24' font-weight='600'>{escape(domain.title())} Metrics</text>",
            ]

            for index, (stat_name, value, original) in enumerate(numeric_stats):
                label = stat_name.replace("_", " ").title()
                y = top_padding + index * (bar_height + spacing)
                bar_width = 0 if max_value == 0 else (value / max_value) * chart_width
                svg_parts.extend(
                    [
                        f"<text x='{left_padding - 12}' y='{y + bar_height / 1.5}' text-anchor='end' fill='#cbd5f5' font-size='14'>{escape(label)}</text>",
                        f"<rect x='{left_padding}' y='{y}' width='{bar_width}' height='{bar_height}' rx='10' fill='url(#barGradient)' />",
                        f"<text x='{left_padding + bar_width + 12}' y='{y + bar_height / 1.5}' fill='#f8fafc' font-size='14'>{_format_metric_value(original)}</text>",
                    ]
                )

            svg_parts.append("</svg>")

            chart_path.write_text("".join(svg_parts), encoding="utf-8")
            created.append((domain, chart_path))

            console.log("Chart created", f"domain={domain}", f"path={chart_path}")

        return created

    def _render_list(self, title: str, items: Iterable[str]) -> str:
        """Render an HTML list section when the content is available."""

        escaped_items = [f"<li>{escape(item)}</li>" for item in items]
        if not escaped_items:
            return ""
        return f"<section><h2>{escape(title)}</h2><ul>{''.join(escaped_items)}</ul></section>"

    def generate_html(self, metrics: MetricSnapshot) -> Path:
        """Create an HTML report complete with charts for numeric metrics."""

        self.ensure_structure()
        charts = self._create_charts(metrics)
        report_path = self.output_dir / "report.html"

        console.log("Writing HTML report", f"path={report_path}")

        summary_items = "".join(
            f"<li><strong>{escape(key.title())}</strong>: {escape(_format_metric_value(value) if isinstance(value, (int, float)) else str(value))}</li>"
            for key, value in metrics.summary.items()
        )

        metrics_sections: List[str] = []
        for domain, stats in metrics.stats.items():
            rows = []
            for name, value in stats.items():
                label = escape(name.replace("_", " ").title())
                display_value = (
                    _format_metric_value(value) if isinstance(value, (int, float)) else str(value)
                )
                rows.append(f"<tr><th>{label}</th><td>{escape(display_value)}</td></tr>")
            if rows:
                metrics_sections.append(
                    f"<section><h3>{escape(domain.title())}</h3><table>{''.join(rows)}</table></section>"
                )

        chart_sections = []
        for domain, chart_path in charts:
            relative_path = chart_path.relative_to(self.output_dir)
            chart_sections.append(
                """
                <figure>
                    <img src="{src}" alt="{alt}" loading="lazy" />
                    <figcaption>{caption}</figcaption>
                </figure>
                """.format(
                    src=escape(str(relative_path).replace("\\", "/")),
                    alt=escape(f"{domain.title()} metrics"),
                    caption=escape(domain.title()),
                )
            )

        html_sections = [
            "<section><h1>GitHub Feedback Report</h1>",
            f"<p><strong>Repository:</strong> {escape(metrics.repo)}</p>",
            f"<p><strong>Period:</strong> {escape(str(metrics.months))} months</p>",
            "</section>",
        ]

        if summary_items:
            html_sections.append(f"<section><h2>Summary</h2><ul>{summary_items}</ul></section>")
        if metrics_sections:
            html_sections.append("<section><h2>Metrics</h2>" + "".join(metrics_sections) + "</section>")
        if chart_sections:
            html_sections.append("<section><h2>Visual Highlights</h2>" + "".join(chart_sections) + "</section>")

        if metrics.highlights:
            html_sections.append(self._render_list("Growth Highlights", metrics.highlights))
        if metrics.spotlight_examples:
            for category, entries in metrics.spotlight_examples.items():
                html_sections.append(
                    self._render_list(f"Spotlight — {category.replace('_', ' ').title()}", entries)
                )
        if metrics.yearbook_story:
            paragraphs = "".join(f"<p>{escape(paragraph)}</p>" for paragraph in metrics.yearbook_story)
            html_sections.append(f"<section><h2>Year in Review</h2>{paragraphs}</section>")
        if metrics.awards:
            awards_html = f"<section><h2>🏆 Awards Cabinet</h2>"
            awards_html += f"<p><strong>총 {len(metrics.awards)}개의 어워드를 획득했습니다!</strong></p>"

            # Categorize awards
            categories = self._categorize_awards(metrics.awards)

            for category_name, category_awards in categories.items():
                if category_awards:
                    awards_html += f"<h3>{escape(category_name)}</h3>"
                    awards_html += "<ul>"
                    for award in category_awards:
                        awards_html += f"<li>{escape(award)}</li>"
                    awards_html += "</ul>"

            awards_html += "</section>"
            html_sections.append(awards_html)

        evidence_sections = []
        for domain, links in metrics.evidence.items():
            link_items = "".join(
                f"<li><a href='{escape(link)}' target='_blank' rel='noopener'>{escape(link)}</a></li>"
                for link in links
            )
            if link_items:
                evidence_sections.append(
                    f"<section><h3>{escape(domain.title())}</h3><ul>{link_items}</ul></section>"
                )
        if evidence_sections:
            html_sections.append("<section><h2>Evidence</h2>" + "".join(evidence_sections) + "</section>")

        html_report = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>GitHub Feedback Report — {escape(metrics.repo)}</title>
    <style>
        :root {{
            color-scheme: light dark;
            font-family: 'Segoe UI', Roboto, sans-serif;
            background-color: #0f172a;
            color: #e2e8f0;
        }}
        body {{
            margin: 0 auto;
            max-width: 960px;
            padding: 2rem 1.5rem 4rem;
            line-height: 1.6;
        }}
        section {{
            margin-bottom: 2rem;
            background: rgba(15, 23, 42, 0.6);
            padding: 1.5rem;
            border-radius: 1rem;
            box-shadow: 0 10px 30px rgba(15, 23, 42, 0.35);
        }}
        h1, h2, h3 {{
            margin-top: 0;
            color: #38bdf8;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        th, td {{
            padding: 0.6rem 0.8rem;
            border-bottom: 1px solid rgba(148, 163, 184, 0.2);
            text-align: left;
        }}
        figure {{
            margin: 0;
            display: grid;
            gap: 0.5rem;
            justify-items: center;
        }}
        figure img {{
            max-width: 100%;
            border-radius: 0.75rem;
            background: rgba(148, 163, 184, 0.12);
            padding: 0.5rem;
        }}
        a {{
            color: #38bdf8;
        }}
    </style>
</head>
<body>
    {''.join(html_sections)}
</body>
</html>
"""

        report_path.write_text(html_report, encoding="utf-8")
        return report_path

