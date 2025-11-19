"""Report generation for GitHub feedback analysis."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Protocol, Tuple, Union

from .console import Console
from .constants import AWARD_CATEGORIES, AWARD_KEYWORDS, COLLECTION_LIMITS, DISPLAY_LIMITS
from .game_elements import GameRenderer, LevelCalculator
from .models import (
    CommitMessageFeedback,
    IssueFeedback,
    MetricSnapshot,
    PRTitleFeedback,
    ReviewToneFeedback,
)
from .utils import pad_to_width

console = Console()

# Type alias for feedback data structures
FeedbackData = Union[CommitMessageFeedback, PRTitleFeedback, ReviewToneFeedback, IssueFeedback]


# ============================================================================
# Helper Classes for Report Generation
# ============================================================================

class MarkdownSectionBuilder:
    """Helper class for building markdown sections with common patterns."""

    @staticmethod
    def build_section(
        title: str,
        description: str = "",
        emoji: str = ""
    ) -> List[str]:
        """Build a section header with optional description."""
        lines = []
        header = f"### {emoji} {title}" if emoji else f"### {title}"
        lines.append(header)
        lines.append("")

        if description:
            lines.append(f"> {description}")
            lines.append("")

        return lines

    @staticmethod
    def build_table(headers: List[str], rows: List[List[str]]) -> List[str]:
        """Build a markdown table from headers and rows."""
        lines = []
        lines.append("| " + " | ".join(headers) + " |")
        lines.append("|" + "|".join(["---"] * len(headers)) + "|")

        for row in rows:
            lines.append("| " + " | ".join(str(cell) for cell in row) + " |")

        lines.append("")
        return lines

    @staticmethod
    def build_list(items: List[str], prefix: str = "-") -> List[str]:
        """Build a markdown list from items."""
        return [f"{prefix} {item}" for item in items] + [""]

    @staticmethod
    def build_subsection(
        data_check: Any,
        title: str,
        content_builder: Callable[[], List[str]],
        emoji: str = "",
        description: str = ""
    ) -> List[str]:
        """Build a subsection if data exists, using a content builder function."""
        lines = []
        if data_check:
            lines.extend(MarkdownSectionBuilder.build_section(title, description, emoji))
            lines.extend(content_builder())
        return lines


def _format_metric_value(value: object) -> str:
    """Format numeric values with separators while keeping strings intact."""

    if isinstance(value, bool):
        return str(value)
    if isinstance(value, int):
        return f"{value:,}"
    if isinstance(value, float):
        return f"{value:,.2f}"
    return str(value)


def _escape_table_cell(text: str) -> str:
    """Escape special characters in markdown table cells to prevent table breakage.

    Args:
        text: Text to escape

    Returns:
        Escaped text safe for use in markdown tables
    """
    if not text:
        return text

    # Replace pipe characters that would break table structure
    text = text.replace("|", "\\|")

    # Replace newlines with HTML breaks for multi-line content
    text = text.replace("\n", "<br>")

    # Trim excessive whitespace
    text = " ".join(text.split())

    return text


@dataclass(slots=True)
class Reporter:
    """Create human-readable artefacts from metrics."""

    output_dir: Path = Path("reports")
    _current_repo: Optional[str] = None  # Temporary storage for current repo during report generation
    llm_client: Optional[Any] = None  # Optional LLM client for generating summary quotes
    web_url: str = "https://github.com"  # Base URL for GitHub links (configurable for enterprise)

    def ensure_structure(self) -> None:
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _get_repo_from_context(self) -> str:
        """Get the current repository being processed.

        Returns:
            Repository in 'owner/repo' format, or empty string if not available
        """
        return self._current_repo or ""

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



    def _build_header_and_summary(self, metrics: MetricSnapshot) -> List[str]:
        """Build header and summary section."""
        lines = ["# 🚀 GitHub Feedback Report", ""]

        # Generate witty summary quote if LLM client is available
        if self.llm_client and (metrics.awards or metrics.highlights or metrics.summary):
            try:
                quote = self.llm_client.generate_award_summary_quote(
                    metrics.awards,
                    metrics.highlights,
                    metrics.summary,
                )
                if quote:
                    lines.append(f"> ✨ **{quote}**")
                    lines.append("")
            except Exception as e:
                # Silently skip if quote generation fails
                console.log("Failed to generate award summary quote", f"error={e}")

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
        """Build metrics section (HTML version)."""
        lines = ["## 📊 Detailed Metrics", ""]
        lines.append("> 각 활동 영역별 상세 수치를 확인하세요")
        lines.append("")

        for domain, domain_stats in metrics.stats.items():
            lines.append(f"### {domain.title()}")
            lines.append("")

            # Build table data
            headers = ["지표", "값"]
            rows = []
            for stat_name, stat_value in domain_stats.items():
                formatted_value = (
                    _format_metric_value(stat_value)
                    if isinstance(stat_value, (int, float))
                    else str(stat_value)
                )
                rows.append([stat_name.replace('_', ' ').title(), formatted_value])

            # Render as HTML table
            lines.extend(GameRenderer.render_html_table(
                headers=headers,
                rows=rows,
                title="",
                description="",
                striped=True
            ))

        return lines

    def _build_highlights_section(self, metrics: MetricSnapshot) -> List[str]:
        """Build growth highlights section (HTML version)."""
        if not metrics.highlights:
            return []

        lines = ["## ✨ Growth Highlights", ""]
        lines.append("> 이번 기간 동안의 주요 성과와 성장 포인트")
        lines.append("")

        # Build HTML table
        headers = ["#", "성과"]
        rows = [[str(i), highlight] for i, highlight in enumerate(metrics.highlights, 1)]

        lines.extend(GameRenderer.render_html_table(
            headers=headers,
            rows=rows,
            title="",
            description="",
            striped=True
        ))

        lines.append("---")
        lines.append("")
        return lines

    def _build_spotlight_section(self, metrics: MetricSnapshot) -> List[str]:
        """Build spotlight examples section (HTML version)."""
        if not metrics.spotlight_examples:
            return []

        # Filter out categories with no entries
        non_empty_categories = {
            category: entries
            for category, entries in metrics.spotlight_examples.items()
            if entries
        }

        # If no categories have content, don't create the section
        if not non_empty_categories:
            return []

        lines = ["## 🎯 Spotlight Examples", ""]
        lines.append("> 주목할 만한 기여 사례")
        lines.append("")

        for category, entries in non_empty_categories.items():
            lines.append(f"### {category.replace('_', ' ').title()}")
            lines.append("")

            # Build table data
            headers = ["사례"]
            rows = [[entry] for entry in entries]

            # Render as HTML table
            lines.extend(GameRenderer.render_html_table(
                headers=headers,
                rows=rows,
                title="",
                description="",
                striped=True
            ))

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
                lines.append("| 순간 |")
                lines.append("|------|")
                for moment in metrics.year_end_review.proudest_moments:
                    lines.append(f"| {moment} |")
                lines.append("")

            if metrics.year_end_review.biggest_challenges:
                lines.append("### 💪 극복한 도전들")
                lines.append("")
                lines.append("| 도전 |")
                lines.append("|------|")
                for challenge in metrics.year_end_review.biggest_challenges:
                    lines.append(f"| {challenge} |")
                lines.append("")

            if metrics.year_end_review.lessons_learned:
                lines.append("### 📚 배운 교훈들")
                lines.append("")
                lines.append("| 교훈 |")
                lines.append("|------|")
                for lesson in metrics.year_end_review.lessons_learned:
                    lines.append(f"| {lesson} |")
                lines.append("")

            if metrics.year_end_review.next_year_goals:
                lines.append("### 🎯 내년 목표")
                lines.append("")
                lines.append("| 목표 |")
                lines.append("|------|")
                for goal in metrics.year_end_review.next_year_goals:
                    lines.append(f"| {goal} |")
                lines.append("")

        lines.append("---")
        lines.append("")
        return lines


    def _build_skill_tree_section(self, metrics: MetricSnapshot) -> List[str]:
        """Build skill tree section showing acquired and available skills."""
        lines = ["## 🎮 스킬 트리", ""]
        lines.append("> 획득한 스킬과 습득 가능한 스킬을 확인하세요")
        lines.append("")

        # Collect acquired skills (from awards and highlights)
        acquired_skills = []
        available_skills = []
        growing_skills = []

        # 1. Acquired Skills - from top awards and strengths
        if metrics.awards:
            for award in metrics.awards[:3]:
                # Determine mastery based on award position
                mastery = 100 - (metrics.awards.index(award) * 10)
                acquired_skills.append({
                    "name": award,
                    "type": "패시브",
                    "mastery": mastery,
                    "effect": "지속적으로 발휘되는 강점",
                    "evidence": [award],
                    "emoji": "💎"
                })

        # Add skills from highlights
        if metrics.highlights and len(acquired_skills) < 5:
            remaining = 5 - len(acquired_skills)
            for highlight in metrics.highlights[:remaining]:
                acquired_skills.append({
                    "name": highlight.split('.')[0],
                    "type": "액티브",
                    "mastery": 80,
                    "effect": "의식적으로 활용하는 능력",
                    "evidence": [highlight],
                    "emoji": "✨"
                })

        # Add coding habits as acquired skills if quality is high
        if metrics.detailed_feedback and len(acquired_skills) < 5:
            # Commit message mastery
            if metrics.detailed_feedback.commit_feedback:
                cf = metrics.detailed_feedback.commit_feedback
                if cf.total_commits > 0:
                    quality_ratio = cf.good_messages / cf.total_commits
                    if quality_ratio >= 0.7:  # 70% or better
                        mastery = min(100, int(quality_ratio * 100))
                        acquired_skills.append({
                            "name": "명확한 커밋 메시지 작성",
                            "type": "패시브",
                            "mastery": mastery,
                            "effect": f"전체 커밋의 {int(quality_ratio * 100)}%가 명확하고 의미있는 메시지",
                            "evidence": [f"{cf.good_messages}/{cf.total_commits} 커밋이 높은 품질"],
                            "emoji": "📝"
                        })

            # PR title mastery
            if metrics.detailed_feedback.pr_title_feedback and len(acquired_skills) < 5:
                pf = metrics.detailed_feedback.pr_title_feedback
                if pf.total_prs > 0:
                    quality_ratio = pf.clear_titles / pf.total_prs
                    if quality_ratio >= 0.7:  # 70% or better
                        mastery = min(100, int(quality_ratio * 100))
                        acquired_skills.append({
                            "name": "명확한 PR 제목 작성",
                            "type": "패시브",
                            "mastery": mastery,
                            "effect": f"전체 PR의 {int(quality_ratio * 100)}%가 명확하고 구체적",
                            "evidence": [f"{pf.clear_titles}/{pf.total_prs} PR이 높은 품질"],
                            "emoji": "🔀"
                        })

            # Review tone mastery
            if metrics.detailed_feedback.review_tone_feedback and len(acquired_skills) < 5:
                rtf = metrics.detailed_feedback.review_tone_feedback
                total_reviews = rtf.constructive_reviews + rtf.harsh_reviews + rtf.neutral_reviews
                if total_reviews > 0:
                    quality_ratio = rtf.constructive_reviews / total_reviews
                    if quality_ratio >= 0.7:  # 70% or better
                        mastery = min(100, int(quality_ratio * 100))
                        acquired_skills.append({
                            "name": "건설적인 리뷰 작성",
                            "type": "패시브",
                            "mastery": mastery,
                            "effect": f"전체 리뷰의 {int(quality_ratio * 100)}%가 건설적이고 도움이 됨",
                            "evidence": [f"{rtf.constructive_reviews}/{total_reviews} 리뷰가 높은 품질"],
                            "emoji": "👀"
                        })

        # 2. Available Skills - from improvement suggestions
        if metrics.detailed_feedback:
            if metrics.detailed_feedback.commit_feedback and hasattr(metrics.detailed_feedback.commit_feedback, 'suggestions'):
                for suggestion in metrics.detailed_feedback.commit_feedback.suggestions[:2]:
                    available_skills.append({
                        "name": "커밋 메시지 향상",
                        "type": "미습득",
                        "mastery": 40,
                        "effect": suggestion,
                        "evidence": [suggestion],
                        "emoji": "📝"
                    })

            if metrics.detailed_feedback.pr_title_feedback and hasattr(metrics.detailed_feedback.pr_title_feedback, 'suggestions'):
                for suggestion in metrics.detailed_feedback.pr_title_feedback.suggestions[:2]:
                    available_skills.append({
                        "name": "PR 제목 최적화",
                        "type": "미습득",
                        "mastery": 40,
                        "effect": suggestion,
                        "evidence": [suggestion],
                        "emoji": "🔀"
                    })

            if metrics.detailed_feedback.review_tone_feedback and hasattr(metrics.detailed_feedback.review_tone_feedback, 'suggestions'):
                for suggestion in metrics.detailed_feedback.review_tone_feedback.suggestions[:2]:
                    available_skills.append({
                        "name": "건설적인 리뷰 작성",
                        "type": "미습득",
                        "mastery": 40,
                        "effect": suggestion,
                        "evidence": [suggestion],
                        "emoji": "👀"
                    })

        # 3. Growing Skills - from retrospective positive patterns
        if metrics.retrospective and hasattr(metrics.retrospective, 'behavior_patterns'):
            positive_patterns = [bp for bp in metrics.retrospective.behavior_patterns if bp.impact == "positive"]
            for pattern in positive_patterns[:3]:
                growing_skills.append({
                    "name": pattern.description,
                    "type": "성장중",
                    "mastery": 60,
                    "effect": "빠르게 발전하고 있는 영역",
                    "evidence": [pattern.description],
                    "emoji": "🌱"
                })

        # Render acquired skills
        if acquired_skills:
            lines.append("### 💎 획득한 스킬 (Acquired Skills)")
            lines.append("")
            for skill in acquired_skills:
                lines.extend(GameRenderer.render_skill_card(
                    skill["name"],
                    skill["type"],
                    skill["mastery"],
                    skill["effect"],
                    skill["evidence"],
                    skill["emoji"]
                ))

        # Render growing skills
        if growing_skills:
            lines.append("### 🌱 성장 중인 스킬 (Growing Skills)")
            lines.append("")
            for skill in growing_skills:
                lines.extend(GameRenderer.render_skill_card(
                    skill["name"],
                    skill["type"],
                    skill["mastery"],
                    skill["effect"],
                    skill["evidence"],
                    skill["emoji"]
                ))

        # Render available skills
        if available_skills:
            lines.append("### 🎯 습득 가능한 스킬 (Available Skills)")
            lines.append("")
            for skill in available_skills[:3]:  # Limit to top 3
                lines.extend(GameRenderer.render_skill_card(
                    skill["name"],
                    skill["type"],
                    skill["mastery"],
                    skill["effect"],
                    skill["evidence"],
                    skill["emoji"]
                ))

        lines.append("---")
        lines.append("")
        return lines

    def _build_summary_overview_table(self, metrics: MetricSnapshot) -> List[str]:
        """Build integrated summary table with strengths, areas for improvement, and growth."""
        lines = ["## 📊 한눈에 보는 요약", ""]
        lines.append("> 잘하고 있는 것, 보완하면 좋을 것, 성장한 점을 한눈에 확인하세요")
        lines.append("")

        lines.append("| 구분 | 내용 |")
        lines.append("|------|------|")

        # 1. 잘하고 있는 것 (Strengths) - from awards and highlights
        strengths = []

        # Get top awards (max 3)
        if metrics.awards:
            top_awards = metrics.awards[:3]
            strengths.extend([f"🏆 {award}" for award in top_awards])

        # Get key highlights if we need more (max 3 total)
        if len(strengths) < 3 and metrics.highlights:
            remaining = 3 - len(strengths)
            for highlight in metrics.highlights[:remaining]:
                # Shorten highlight to first sentence or 80 chars
                short_highlight = highlight.split('.')[0][:80]
                if len(highlight.split('.')[0]) > 80:
                    short_highlight += "..."
                strengths.append(f"✨ {short_highlight}")

        # Add strengths to table
        if strengths:
            strengths_text = "<br>".join(strengths)
            lines.append(f"| **✅ 잘하고 있는 것** | {strengths_text} |")
        else:
            lines.append("| **✅ 잘하고 있는 것** | 활동을 분석 중입니다 |")

        # 2. 보완하면 좋을 것 (Areas for Improvement) - from detailed feedback suggestions
        improvements = []

        if metrics.detailed_feedback:
            # Collect suggestions from all feedback types
            if metrics.detailed_feedback.commit_feedback and hasattr(metrics.detailed_feedback.commit_feedback, 'suggestions'):
                improvements.extend([f"📝 {s}" for s in metrics.detailed_feedback.commit_feedback.suggestions[:2]])

            if len(improvements) < 3 and metrics.detailed_feedback.pr_title_feedback and hasattr(metrics.detailed_feedback.pr_title_feedback, 'suggestions'):
                remaining = 3 - len(improvements)
                improvements.extend([f"🔀 {s}" for s in metrics.detailed_feedback.pr_title_feedback.suggestions[:remaining]])

            if len(improvements) < 3 and metrics.detailed_feedback.review_tone_feedback and hasattr(metrics.detailed_feedback.review_tone_feedback, 'suggestions'):
                remaining = 3 - len(improvements)
                improvements.extend([f"👀 {s}" for s in metrics.detailed_feedback.review_tone_feedback.suggestions[:remaining]])

        # Add improvement areas to table
        if improvements:
            improvements_text = "<br>".join(improvements[:3])
            lines.append(f"| **💡 보완하면 좋을 것** | {improvements_text} |")
        else:
            lines.append("| **💡 보완하면 좋을 것** | 전반적으로 좋은 품질을 유지하고 있습니다 |")

        # 3. 성장한 점 (Growth) - from retrospective and highlights
        growth_points = []

        # Get from retrospective if available
        if metrics.retrospective:
            # Use time comparisons showing positive growth
            if hasattr(metrics.retrospective, 'time_comparisons') and metrics.retrospective.time_comparisons:
                for tc in metrics.retrospective.time_comparisons[:2]:
                    if tc.direction == "increasing" and tc.significance in ["major", "moderate"]:
                        growth_points.append(f"📈 {tc.metric_name} {tc.change_percentage:+.0f}% 증가")

            # Use behavior patterns with positive impact
            if len(growth_points) < 3 and hasattr(metrics.retrospective, 'behavior_patterns') and metrics.retrospective.behavior_patterns:
                remaining = 3 - len(growth_points)
                positive_patterns = [bp for bp in metrics.retrospective.behavior_patterns if bp.impact == "positive"]
                for pattern in positive_patterns[:remaining]:
                    short_desc = pattern.description[:60]
                    if len(pattern.description) > 60:
                        short_desc += "..."
                    growth_points.append(f"🧠 {short_desc}")

        # Fallback to highlights
        if len(growth_points) < 3 and metrics.highlights:
            remaining = 3 - len(growth_points)
            for highlight in metrics.highlights[:remaining]:
                short_highlight = highlight.split('.')[0][:60]
                if len(highlight.split('.')[0]) > 60:
                    short_highlight += "..."
                growth_points.append(f"✨ {short_highlight}")

        # Add growth points to table
        if growth_points:
            growth_text = "<br>".join(growth_points[:3])
            lines.append(f"| **🌱 성장한 점** | {growth_text} |")
        else:
            lines.append("| **🌱 성장한 점** | 꾸준한 활동으로 성장하고 있습니다 |")

        lines.append("")
        lines.append("---")
        lines.append("")
        return lines

    def _build_awards_section(self, metrics: MetricSnapshot) -> List[str]:
        """Build awards cabinet section (HTML version)."""
        if not metrics.awards:
            return []

        lines = ["## 🏆 Awards Cabinet", ""]
        lines.append(f"**총 {len(metrics.awards)}개의 어워드를 획득했습니다!**")
        lines.append("")

        categories = self._categorize_awards(metrics.awards)

        # Build awards grid with HTML
        awards_data = []
        for category_name, category_awards in categories.items():
            if category_awards:
                # Extract emoji from category name
                emoji = category_name.split()[0] if category_name else "🏆"
                category_title = " ".join(category_name.split()[1:]) if len(category_name.split()) > 1 else category_name

                # Combine all awards in this category
                description = "<br>".join(f"• {award}" for award in category_awards)

                awards_data.append({
                    "category": category_title,
                    "description": description,
                    "emoji": emoji,
                    "count": str(len(category_awards))
                })

        # Render using HTML
        lines.extend(GameRenderer.render_awards_grid(awards_data, columns=2))

        lines.append("---")
        lines.append("")
        return lines

    def _calculate_repo_character_stats(self, metrics: MetricSnapshot) -> dict:
        """Calculate RPG-style character stats from repository metrics."""
        stats = metrics.stats

        # Extract key metrics with safe defaults
        commits = stats.get("commits", {})
        prs = stats.get("pull_requests", {})
        reviews = stats.get("reviews", {})

        total_commits = commits.get("total", 0)
        total_prs = prs.get("total", 0)
        total_reviews = reviews.get("total", 0)
        merged_prs = prs.get("merged", 0)

        # Code Quality (0-100): Based on PR merge rate, awards, and coding habits
        merge_rate = (merged_prs / total_prs) if total_prs > 0 else 0
        award_count = len(metrics.awards) if metrics.awards else 0

        # Calculate coding habits quality (commit messages + PR titles)
        coding_habits_score = 0
        if metrics.detailed_feedback:
            # Commit message quality
            if metrics.detailed_feedback.commit_feedback:
                cf = metrics.detailed_feedback.commit_feedback
                if cf.total_commits > 0:
                    commit_quality_ratio = cf.good_messages / cf.total_commits
                    coding_habits_score += commit_quality_ratio * 50  # 0-50 points

            # PR title quality
            if metrics.detailed_feedback.pr_title_feedback:
                pf = metrics.detailed_feedback.pr_title_feedback
                if pf.total_prs > 0:
                    pr_title_quality_ratio = pf.clear_titles / pf.total_prs
                    coding_habits_score += pr_title_quality_ratio * 50  # 0-50 points

            # Normalize to 0-20 range
            coding_habits_score = min(20, coding_habits_score / 5)

        code_quality = min(100, int(
            (merge_rate * 35) +  # Merge success rate (0-35)
            (min(award_count / 15, 1) * 25) +  # Award achievement (0-25)
            (20 if total_commits >= 100 else (total_commits / 100) * 20) +  # Experience (0-20)
            coding_habits_score  # Coding habits (0-20)
        ))

        # Collaboration (0-100): Based on reviews, PR engagement, and review tone
        collab_network = metrics.collaboration
        unique_collaborators = collab_network.unique_collaborators if collab_network else 0
        review_count = collab_network.review_received_count if collab_network else 0

        # Calculate review tone quality
        review_tone_score = 0
        if metrics.detailed_feedback and metrics.detailed_feedback.review_tone_feedback:
            rtf = metrics.detailed_feedback.review_tone_feedback
            total_tone_reviews = rtf.constructive_reviews + rtf.harsh_reviews + rtf.neutral_reviews
            if total_tone_reviews > 0:
                # Constructive reviews contribute positively, harsh reviews reduce score
                constructive_ratio = rtf.constructive_reviews / total_tone_reviews
                harsh_ratio = rtf.harsh_reviews / total_tone_reviews
                review_tone_score = (constructive_ratio - (harsh_ratio * 0.5)) * 20  # 0-20 points
                review_tone_score = max(0, min(20, review_tone_score))  # Clamp to 0-20

        collaboration = min(100, int(
            (min(total_reviews / 30, 1) * 35) +  # Review activity (0-35)
            (min(unique_collaborators / 15, 1) * 30) +  # Network size (0-30)
            (15 if review_count >= 50 else (review_count / 50) * 15) +  # Review received (0-15)
            review_tone_score  # Review tone quality (0-20)
        ))

        # Problem Solving (0-100): Based on PR diversity and tech stack
        tech_stack = metrics.tech_stack
        tech_diversity = tech_stack.diversity_score if tech_stack else 0
        language_count = len(tech_stack.top_languages) if tech_stack and tech_stack.top_languages else 0

        problem_solving = min(100, int(
            (min(total_prs / 25, 1) * 40) +  # PR production (0-40) - 기준 상향
            (tech_diversity * 35) +  # Technology breadth (0-35)
            (min(language_count / 7, 1) * 25)  # Language variety (0-25) - 기준 상향
        ))

        # Productivity (0-100): Based on total activity volume
        total_activity = total_commits + total_prs + total_reviews
        monthly_velocity = total_activity / metrics.months if metrics.months > 0 else 0

        productivity = min(100, int(
            (min(total_commits / 150, 1) * 35) +  # Commit volume (0-35) - 기준 상향
            (min(total_prs / 50, 1) * 35) +  # PR volume (0-35) - 기준 상향
            (min(monthly_velocity / 30, 1) * 30)  # Velocity (0-30) - 기준 상향
        ))

        # Growth (0-100): Based on highlights and retrospective insights
        highlight_count = len(metrics.highlights) if metrics.highlights else 0
        has_retrospective = metrics.retrospective is not None

        # Check for positive growth trends
        growth_indicators = 0
        if metrics.retrospective and hasattr(metrics.retrospective, 'time_comparisons'):
            positive_trends = sum(1 for tc in metrics.retrospective.time_comparisons
                                if tc.direction == "increasing")
            growth_indicators = min(positive_trends, 5)

        growth = min(100, int(
            30 +  # Base growth score - 기준 하향 (50->30)
            (min(highlight_count / 8, 1) * 25) +  # Highlights (0-25) - 기준 상향
            (15 if has_retrospective else 0) +  # Deep analysis bonus (0-15)
            (growth_indicators * 6)  # Positive trend bonus (0-30) - 보너스 증대
        ))

        return {
            "code_quality": code_quality,
            "collaboration": collaboration,
            "problem_solving": problem_solving,
            "productivity": productivity,
            "growth": growth,
        }

    def _render_repo_character_stats(self, metrics: MetricSnapshot) -> List[str]:
        """Render RPG-style character stats visualization for repository (티어 시스템 사용)."""
        lines: List[str] = []

        stats = self._calculate_repo_character_stats(metrics)
        avg_stat = sum(stats.values()) / len(stats) if stats else 0

        # 티어 시스템으로 등급 계산
        tier, title, rank_emoji = LevelCalculator.calculate_tier(avg_stat)

        # 특성 타이틀 결정
        specialty_title = LevelCalculator.get_specialty_title(stats)

        # 활동량 데이터
        total_commits = metrics.stats.get("commits", {}).get("total", 0)
        total_prs = metrics.stats.get("pull_requests", {}).get("total", 0)

        # 뱃지 생성
        badges = LevelCalculator.get_badges_from_stats(
            stats,
            total_commits=total_commits,
            total_prs=total_prs,
            total_repos=0  # 일반 보고서는 단일 저장소
        )

        # 저장소 특화 뱃지 추가
        if stats.get("growth", 0) >= 80:
            # "🚀 급성장 개발자"를 "🚀 급성장 저장소"로 교체
            badges = [b.replace("급성장 개발자", "급성장 저장소") for b in badges]

        # GameRenderer로 캐릭터 스탯 렌더링
        lines.append("## 🎮 저장소 캐릭터 스탯")
        lines.append("")
        lines.append("> 저장소의 활동을 RPG 캐릭터 스탯으로 시각화")
        lines.append("")

        character_lines = GameRenderer.render_character_stats(
            level=tier,
            title=title,
            rank_emoji=rank_emoji,
            specialty_title=specialty_title,
            stats=stats,
            experience_data={},  # 경험치 데이터 없음
            badges=badges,
            use_tier_system=True  # 티어 시스템 사용
        )

        lines.extend(character_lines)
        lines.append("---")
        lines.append("")
        return lines

    def _build_detailed_feedback_section(self, metrics: MetricSnapshot) -> List[str]:
        """Build detailed feedback section."""
        if not metrics.detailed_feedback:
            return []

        feedback = metrics.detailed_feedback

        # Check if there's any actual feedback content
        has_content = any([
            feedback.commit_feedback,
            feedback.pr_title_feedback,
            feedback.review_tone_feedback,
            feedback.issue_feedback
        ])

        # If no feedback content exists, don't create the section
        if not has_content:
            return []

        lines = ["## 💡 코딩 습관 평가 및 스킬 향상 가이드", ""]
        lines.append("> 커밋 메시지, PR 제목, 리뷰 톤, 이슈 작성 등 코딩 습관을 분석하고 개선 방향을 제시합니다")
        lines.append("")

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
        feedback_data: FeedbackData,
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

        # Build summary statistics as a table
        total_attr, total_label, unit = stats_config.get('total', (None, None, '개'))
        good_attr, good_label, _ = stats_config.get('good', (None, None, '개'))
        poor_attr, poor_label, _ = stats_config.get('poor', (None, None, '개'))

        total_value = getattr(feedback_data, total_attr, 0) if total_attr else 0
        good_value = getattr(feedback_data, good_attr, 0) if good_attr else 0
        poor_value = getattr(feedback_data, poor_attr, 0) if poor_attr else 0

        lines.append("| 지표 | 값 |")
        lines.append("|------|-----|")

        if total_value > 0:
            good_pct = (good_value / total_value) * 100
            lines.append(f"| {total_label} | {total_value:,}{unit} |")
            lines.append(f"| {good_label} | {good_value:,}{unit} ({good_pct:.1f}%) |")
            lines.append(f"| {poor_label} | {poor_value:,}{unit} |")

            # Add additional stats if configured
            for key, (attr, label, stat_unit) in stats_config.items():
                if key not in ('total', 'good', 'poor'):
                    value = getattr(feedback_data, attr, 0)
                    lines.append(f"| {label} | {value:,}{stat_unit} |")
        else:
            lines.append(f"| {total_label} | {total_value} |")
            lines.append(f"| {good_label} | {good_value} |")
            lines.append(f"| {poor_label} | {poor_value} |")

            # Add additional stats if configured
            for key, (attr, label, stat_unit) in stats_config.items():
                if key not in ('total', 'good', 'poor'):
                    value = getattr(feedback_data, attr, 0)
                    lines.append(f"| {label} | {value} |")
        lines.append("")

        # Suggestions section
        if hasattr(feedback_data, 'suggestions') and feedback_data.suggestions:
            lines.append("#### 💡 개선 제안")
            lines.append("")
            lines.append("| # | 제안 |")
            lines.append("|---|------|")
            for i, suggestion in enumerate(feedback_data.suggestions, 1):
                lines.append(f"| {i} | {suggestion} |")
            lines.append("")

        # Good examples section
        if hasattr(feedback_data, 'examples_good') and feedback_data.examples_good:
            lines.append("#### ✅ 좋은 예시")
            lines.append("")
            lines.append("| 예시 |")
            lines.append("|------|")
            for example in feedback_data.examples_good[:DISPLAY_LIMITS['feedback_examples']]:
                if example_formatter:
                    lines.append(f"| {example_formatter(example)} |")
                elif isinstance(example, dict):
                    lines.append(f"| {example} |")
                else:
                    lines.append(f"| {example} |")
            lines.append("")

        # Poor/improve examples section
        poor_examples = getattr(feedback_data, examples_poor_attr, None)
        if poor_examples:
            lines.append("#### ⚠️ 개선이 필요한 예시")
            lines.append("")
            lines.append("| 예시 |")
            lines.append("|------|")
            for example in poor_examples[:DISPLAY_LIMITS['feedback_examples']]:
                if example_formatter:
                    lines.append(f"| {example_formatter(example)} |")
                elif isinstance(example, dict):
                    lines.append(f"| {example} |")
                else:
                    lines.append(f"| {example} |")
            lines.append("")

        return lines

    def _build_feedback_table(
        self,
        title: str,
        feedback_data,
        good_category: str,
        poor_category: str,
        fallback_good_msg: str,
        fallback_poor_msg: str,
        evidence_formatter,
        link_formatter,
    ) -> List[str]:
        """Build a common feedback table format (HTML version).

        Args:
            title: Section title
            feedback_data: Feedback data object
            good_category: Category label for good examples
            poor_category: Category label for poor examples
            fallback_good_msg: Fallback message for non-dict good examples
            fallback_poor_msg: Fallback message for non-dict poor examples
            evidence_formatter: Function to format evidence from example dict
            link_formatter: Function to format link from example dict

        Returns:
            List of markdown lines
        """
        lines = [title, ""]

        # Build table rows
        headers = ["장점 혹은 개선점/보완점", "근거 (코드, 메세지 등)", "링크"]
        rows = []

        # Add good examples as strengths (장점)
        if hasattr(feedback_data, 'examples_good') and feedback_data.examples_good:
            for example in feedback_data.examples_good[:DISPLAY_LIMITS['feedback_examples']]:
                if isinstance(example, dict):
                    category = f"<strong>장점</strong>: {good_category}"
                    evidence = evidence_formatter(example)
                    link = link_formatter(example)
                    rows.append([category, evidence, link])
                else:
                    example_escaped = _escape_table_cell(str(example))
                    rows.append([f"<strong>장점</strong>: {fallback_good_msg}", example_escaped, "-"])

        # Add poor examples as improvement areas (개선점)
        if hasattr(feedback_data, 'examples_poor') and feedback_data.examples_poor:
            for example in feedback_data.examples_poor[:DISPLAY_LIMITS['feedback_examples']]:
                if isinstance(example, dict):
                    category = f"<strong>개선점</strong>: {poor_category}"
                    evidence = evidence_formatter(example)
                    link = link_formatter(example)
                    rows.append([category, evidence, link])
                else:
                    example_escaped = _escape_table_cell(str(example))
                    rows.append([f"<strong>개선점</strong>: {fallback_poor_msg}", example_escaped, "-"])

        # Handle improve examples (for review tone feedback)
        if hasattr(feedback_data, 'examples_improve') and feedback_data.examples_improve:
            for example in feedback_data.examples_improve[:DISPLAY_LIMITS['feedback_examples']]:
                if isinstance(example, dict):
                    category = f"<strong>개선점</strong>: {poor_category}"
                    evidence = evidence_formatter(example)
                    link = link_formatter(example)
                    rows.append([category, evidence, link])
                else:
                    example_escaped = _escape_table_cell(str(example))
                    rows.append([f"<strong>개선점</strong>: {fallback_poor_msg}", example_escaped, "-"])

        # Add suggestions as additional improvement areas
        if hasattr(feedback_data, 'suggestions') and feedback_data.suggestions:
            for suggestion in feedback_data.suggestions[:3]:  # Limit to 3 suggestions
                suggestion_escaped = _escape_table_cell(suggestion)
                rows.append([f"<strong>보완점</strong>: {suggestion_escaped}", "전반적인 패턴 분석 결과", "-"])

        # Render as HTML table
        lines.extend(GameRenderer.render_html_table(
            headers=headers,
            rows=rows,
            title="",
            description="",
            striped=True
        ))

        return lines

    def _build_commit_feedback(self, commit_feedback) -> List[str]:
        """Build commit feedback subsection with new table format."""
        def format_commit_evidence(example):
            message = example.get('message', '')
            reason = example.get('reason', '')
            suggestion = example.get('suggestion', '')

            # Escape special characters to prevent table breakage
            message_escaped = _escape_table_cell(message)
            reason_escaped = _escape_table_cell(reason)
            suggestion_escaped = _escape_table_cell(suggestion)

            # Build detailed evidence with message, reason, and suggestion
            parts = [f"**메시지**: `{message_escaped}`"]
            if reason_escaped:
                parts.append(f"<br>**근거**: {reason_escaped}")
            if suggestion_escaped:
                parts.append(f"<br>**개선방안**: {suggestion_escaped}")

            return "<br>".join(parts)

        def format_commit_link(example):
            if example.get('url'):
                sha_short = example.get('sha', '')[:7]
                url = _escape_table_cell(example.get('url', ''))
                return f"[{sha_short}]({url})"
            return example.get('sha', '')[:7]

        return self._build_feedback_table(
            title="### 📝 커밋 메시지 품질",
            feedback_data=commit_feedback,
            good_category="명확하고 의미있는 커밋 메시지",
            poor_category="커밋 메시지 구체화 필요",
            fallback_good_msg="좋은 커밋 메시지",
            fallback_poor_msg="커밋 메시지 개선 필요",
            evidence_formatter=format_commit_evidence,
            link_formatter=format_commit_link,
        )

    def _build_pr_title_feedback(self, pr_title_feedback) -> List[str]:
        """Build PR title feedback subsection with new table format."""
        def format_pr_evidence(example):
            title = example.get('title', '')
            reason = example.get('reason', '')
            suggestion = example.get('suggestion', '')

            # Escape special characters to prevent table breakage
            title_escaped = _escape_table_cell(title)
            reason_escaped = _escape_table_cell(reason)
            suggestion_escaped = _escape_table_cell(suggestion)

            # Build detailed evidence with title and reason
            parts = [f"**제목**: `{title_escaped}`"]
            if reason_escaped:
                parts.append(f"<br>**근거**: {reason_escaped}")
            if suggestion_escaped:
                parts.append(f"<br>**개선방안**: {suggestion_escaped}")

            return "<br>".join(parts)

        def format_pr_link(example):
            url = example.get('url', '')
            number = example.get('number', '')

            if url:
                url_escaped = _escape_table_cell(url)
                return f"[#{number}]({url_escaped})" if number else f"[PR]({url_escaped})"
            elif number:
                # Fallback: construct URL if not provided
                return f"[#{number}]({self.web_url}/{self._get_repo_from_context()}/pull/{number})"
            return "-"

        return self._build_feedback_table(
            title="### 🔀 PR 제목 품질",
            feedback_data=pr_title_feedback,
            good_category="명확하고 구체적인 PR 제목",
            poor_category="PR 제목 구체화 필요",
            fallback_good_msg="좋은 PR 제목",
            fallback_poor_msg="PR 제목 개선 필요",
            evidence_formatter=format_pr_evidence,
            link_formatter=format_pr_link,
        )

    def _build_review_tone_feedback(self, review_tone_feedback) -> List[str]:
        """Build review tone feedback subsection with new table format."""
        def format_review_evidence(example):
            # Get the comment/body
            comment = example.get('comment', example.get('body', ''))
            strengths = example.get('strengths', [])
            issues = example.get('issues', [])
            improved_version = example.get('improved_version', '')

            # Escape special characters
            comment_escaped = _escape_table_cell(comment[:150] + "..." if len(comment) > 150 else comment)

            # Build detailed evidence
            parts = [f"**리뷰 코멘트**: `{comment_escaped}`"]

            # Add strengths for good examples
            if strengths:
                strengths_text = "<br>".join(f"• {_escape_table_cell(s)}" for s in strengths[:3])
                parts.append(f"<br>**장점**: <br>{strengths_text}")

            # Add issues for examples that need improvement
            if issues:
                issues_text = "<br>".join(f"• {_escape_table_cell(i)}" for i in issues[:3])
                parts.append(f"<br>**문제점**: <br>{issues_text}")

            # Add improved version if available
            if improved_version:
                improved_escaped = _escape_table_cell(improved_version[:150] + "..." if len(improved_version) > 150 else improved_version)
                parts.append(f"<br>**개선 예시**: `{improved_escaped}`")

            return "<br>".join(parts)

        def format_review_link(example):
            url = example.get('url', '')
            pr_number = example.get('pr_number', '')

            if url:
                url_escaped = _escape_table_cell(url)
                return f"[PR #{pr_number}]({url_escaped})"
            elif pr_number:
                return f"PR #{pr_number}"
            return "-"

        return self._build_feedback_table(
            title="### 👀 리뷰 톤 분석",
            feedback_data=review_tone_feedback,
            good_category="건설적이고 도움이 되는 리뷰",
            poor_category="리뷰 톤 개선 필요",
            fallback_good_msg="좋은 리뷰 톤",
            fallback_poor_msg="리뷰 톤 개선 필요",
            evidence_formatter=format_review_evidence,
            link_formatter=format_review_link,
        )

    def _build_issue_feedback(self, issue_feedback) -> List[str]:
        """Build issue feedback subsection with new table format."""
        def format_issue_evidence(example):
            title = _escape_table_cell(example.get('title', ''))
            return f"#{example.get('number', '')}: `{title}`"

        def format_issue_link(example):
            if example.get('url'):
                url = _escape_table_cell(example.get('url', ''))
                return f"[이슈 보기]({url})"
            return "-"

        return self._build_feedback_table(
            title="### 🐛 이슈 품질",
            feedback_data=issue_feedback,
            good_category="명확하고 상세한 이슈 작성",
            poor_category="이슈 설명 보완 필요",
            fallback_good_msg="좋은 이슈 작성",
            fallback_poor_msg="이슈 설명 개선 필요",
            evidence_formatter=format_issue_evidence,
            link_formatter=format_issue_link,
        )

    def _build_monthly_trends_section(self, metrics: MetricSnapshot) -> List[str]:
        """Build monthly trends section (HTML version with charts)."""
        if not metrics.monthly_trends:
            return []

        lines = ["## 📈 Monthly Trends", ""]
        lines.append("> 월별 활동 패턴과 트렌드 분석")
        lines.append("")

        # Insights as info box
        if metrics.monthly_insights and metrics.monthly_insights.insights:
            insights_text = "\n".join(f"{i}. {insight}" for i, insight in enumerate(metrics.monthly_insights.insights, 1))
            lines.extend(GameRenderer.render_info_box(
                title="주요 인사이트",
                content=insights_text,
                emoji="💡",
                bg_color="#fffbeb",
                border_color="#f59e0b"
            ))

        # Render activity chart
        monthly_chart_data = []
        for trend in metrics.monthly_trends:
            total_activity = trend.commits + trend.pull_requests + trend.reviews + trend.issues
            monthly_chart_data.append({
                "month": trend.month,
                "count": total_activity
            })

        lines.extend(GameRenderer.render_monthly_chart(
            monthly_data=monthly_chart_data,
            title="월별 총 활동량",
            value_key="count",
            label_key="month"
        ))

        # Render detailed data table
        lines.append("### 📊 월별 상세 데이터")
        lines.append("")

        headers = ["월", "커밋", "PR", "리뷰", "이슈", "총 활동"]
        rows = []
        for trend in metrics.monthly_trends:
            total_activity = trend.commits + trend.pull_requests + trend.reviews + trend.issues
            rows.append([
                trend.month,
                str(trend.commits),
                str(trend.pull_requests),
                str(trend.reviews),
                str(trend.issues),
                f"<strong>{total_activity}</strong>"
            ])

        lines.extend(GameRenderer.render_html_table(
            headers=headers,
            rows=rows,
            title="",
            description="",
            striped=True
        ))

        lines.append("---")
        lines.append("")
        return lines

    def _build_tech_stack_section(self, metrics: MetricSnapshot) -> List[str]:
        """Build tech stack section (HTML version)."""
        if not metrics.tech_stack:
            return []

        # Check if there are any languages to display
        if not metrics.tech_stack.top_languages:
            return []

        lines = ["## 💻 Tech Stack Analysis", ""]
        lines.append("> 사용한 기술과 언어 분포")
        lines.append("")
        lines.append(f"**다양성 점수**: {metrics.tech_stack.diversity_score:.2f} (0-1 척도)")
        lines.append("")

        # Build table data
        headers = ["순위", "언어", "파일 수"]
        rows = []
        for i, lang in enumerate(metrics.tech_stack.top_languages[:DISPLAY_LIMITS['top_languages']], 1):
            count = metrics.tech_stack.languages.get(lang, 0)
            rows.append([str(i), lang, f"{count:,}"])

        # Render as HTML table
        lines.extend(GameRenderer.render_html_table(
            headers=headers,
            rows=rows,
            title="",
            description="",
            striped=True
        ))

        lines.append("---")
        lines.append("")
        return lines

    def _build_collaboration_section(self, metrics: MetricSnapshot) -> List[str]:
        """Build PR activity summary section (HTML version)."""
        if not metrics.collaboration:
            return []

        lines = ["## 🤝 PR 활동 요약", ""]
        lines.append("> 함께 성장한 동료들과의 협업")
        lines.append("")

        # Summary table
        headers = ["항목", "값"]
        rows = [
            ["받은 리뷰 수", f"{metrics.collaboration.review_received_count:,}건"],
            ["협업한 사람 수", f"{metrics.collaboration.unique_collaborators:,}명"]
        ]

        lines.extend(GameRenderer.render_html_table(
            headers=headers,
            rows=rows,
            title="",
            description="",
            striped=True
        ))

        if metrics.collaboration.top_reviewers:
            lines.append("### 🌟 주요 리뷰어")
            lines.append("")

            # Top reviewers table
            headers = ["순위", "리뷰어", "리뷰 횟수"]
            rows = []
            for i, reviewer in enumerate(metrics.collaboration.top_reviewers, 1):
                count = metrics.collaboration.pr_reviewers.get(reviewer, 0)
                rows.append([str(i), f"@{reviewer}", f"{count:,}회"])

            lines.extend(GameRenderer.render_html_table(
                headers=headers,
                rows=rows,
                title="",
                description="",
                striped=True
            ))

        lines.append("---")
        lines.append("")
        return lines

    # Evidence Links section removed - links are already embedded in each section
    # where they are relevant (Detailed Feedback, Spotlight Examples, etc.)

    # Removed _build_executive_summary_subsection - already covered in main Executive Summary
    # Removed _build_key_wins_subsection - already covered in Growth Highlights

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
            growth_indicators = '<br>'.join(f"• {ind}" for ind in learning.growth_indicators[:DISPLAY_LIMITS['growth_indicators']]) if learning.growth_indicators else "-"

            rows.append([
                f"{expertise_emoji} {learning.domain}",
                technologies,
                learning.expertise_level,
                growth_indicators
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

    def _build_retrospective_section(self, metrics: MetricSnapshot) -> List[str]:
        """Build comprehensive retrospective analysis section.

        Refactored to use smaller, focused subsection methods for better maintainability.
        """
        if not metrics.retrospective:
            return []

        retro = metrics.retrospective

        # Build all subsections using dedicated methods
        # Note: executive_summary and key_wins removed to avoid duplication with main sections
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

    def generate_markdown(self, metrics: MetricSnapshot) -> Path:
        """Create a markdown report for the provided metrics.

        Improved report structure for better user experience:
        1. Header with basic info
        2. Summary Overview Table - Quick glance at strengths, improvements, and growth
        3. Character Stats - Gamified visualization of repository metrics
        4. Awards Cabinet to celebrate achievements
        5. Growth Highlights to show progress
        6. Monthly Trends for pattern analysis
        7. Detailed Feedback for actionable insights
        8. Deep Retrospective for comprehensive analysis
        9. Spotlight Examples for concrete evidence
        10. Tech Stack to show technical breadth
        """
        self.ensure_structure()
        report_path = self.output_dir / "report.md"

        # Store repo for use in link generation
        self._current_repo = metrics.repo

        console.log("Writing markdown report", f"path={report_path}")

        # Add font styles at the beginning
        font_styles = [
            '<style>',
            '  @import url("https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&display=swap");',
            '  * {',
            '    font-family: "Noto Sans KR", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;',
            '  }',
            '</style>',
            ''
        ]

        # Build all sections in improved order
        sections = [
            # 1. Header with basic info
            self._build_header_and_summary(metrics),
            # 2. Summary Overview Table - NEW! Quick overview
            self._build_summary_overview_table(metrics),
            # 3. Character Stats - NEW! Gamified visualization
            self._render_repo_character_stats(metrics),
            # 4. Skill Tree - NEW! Game-style skill representation
            self._build_skill_tree_section(metrics),
            # 5. Awards Cabinet - Celebrate achievements first!
            self._build_awards_section(metrics),
            # 6. Growth Highlights - Show the story
            self._build_highlights_section(metrics),
            # 7. Monthly Trends - Show patterns
            self._build_monthly_trends_section(metrics),
            # 8. Detailed Feedback - Actionable insights
            self._build_detailed_feedback_section(metrics),
            # 9. Deep Retrospective - Comprehensive analysis
            self._build_retrospective_section(metrics),
            # 10. Spotlight Examples - Concrete evidence
            self._build_spotlight_section(metrics),
            # 11. Tech Stack - Technical breadth
            self._build_tech_stack_section(metrics),
            # Evidence Links section removed - links already embedded in relevant sections
        ]

        # Combine all sections
        all_lines = []
        all_lines.extend(font_styles)  # Add font styles first
        for section in sections:
            all_lines.extend(section)

        try:
            report_path.write_text("\n".join(all_lines), encoding="utf-8")
        except (IOError, OSError) as e:
            raise IOError(f"Failed to write report to {report_path}: {e}") from e

        return report_path

    def generate_markdown_content(self, metrics: MetricSnapshot) -> str:
        """Generate markdown report content without writing to file.

        This is useful for in-memory report generation without creating files.

        Args:
            metrics: Metrics snapshot to generate report from

        Returns:
            Markdown report content as a string
        """
        # Store repo for use in link generation
        self._current_repo = metrics.repo

        # Add font styles at the beginning
        font_styles = [
            '<style>',
            '  @import url("https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&display=swap");',
            '  * {',
            '    font-family: "Noto Sans KR", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;',
            '  }',
            '</style>',
            ''
        ]

        # Build all sections in improved order (same as generate_markdown)
        sections = [
            # 1. Header with basic info
            self._build_header_and_summary(metrics),
            # 2. Summary Overview Table - NEW! Quick overview
            self._build_summary_overview_table(metrics),
            # 3. Character Stats - NEW! Gamified visualization
            self._render_repo_character_stats(metrics),
            # 4. Skill Tree - NEW! Game-style skill representation
            self._build_skill_tree_section(metrics),
            # 5. Awards Cabinet - Celebrate achievements first!
            self._build_awards_section(metrics),
            # 6. Growth Highlights - Show the story
            self._build_highlights_section(metrics),
            # 7. Monthly Trends - Show patterns
            self._build_monthly_trends_section(metrics),
            # 8. Detailed Feedback - Actionable insights
            self._build_detailed_feedback_section(metrics),
            # 9. Deep Retrospective - Comprehensive analysis
            self._build_retrospective_section(metrics),
            # 10. Spotlight Examples - Concrete evidence
            self._build_spotlight_section(metrics),
            # 11. Tech Stack - Technical breadth
            self._build_tech_stack_section(metrics),
            # Evidence Links section removed - links already embedded in relevant sections
        ]

        # Combine all sections
        all_lines = []
        all_lines.extend(font_styles)  # Add font styles first
        for section in sections:
            all_lines.extend(section)

        return "\n".join(all_lines)

