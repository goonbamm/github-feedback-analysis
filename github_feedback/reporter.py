"""Report generation for GitHub feedback analysis."""

from __future__ import annotations

from dataclasses import dataclass
from html import escape
from pathlib import Path
from typing import Iterable, List, Tuple

from .console import Console
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
        categories = {
            "🎖️ 기본 성취": [],
            "⚡ 속도 & 효율성": [],
            "🤝 협업 & 리뷰": [],
            "🎯 품질 & 안정성": [],
            "🎨 특별 기여": [],
            "👑 최고 영예": [],
        }

        for award in awards:
            # Tier awards (Diamond, Platinum, Gold, Silver, Bronze)
            if any(tier in award for tier in ["다이아몬드", "플래티넘", "골드", "실버", "브론즈"]):
                categories["🎖️ 기본 성취"].append(award)
            # Speed and efficiency awards
            elif any(keyword in award for keyword in ["번개", "속도", "스프린터", "스피드", "스프린트", "머신"]):
                categories["⚡ 속도 & 효율성"].append(award)
            # Collaboration awards
            elif any(keyword in award for keyword in ["협업", "리뷰", "멘토", "팀", "지식 전파", "감시자", "챔피언"]):
                categories["🤝 협업 & 리뷰"].append(award)
            # Quality and stability awards
            elif any(keyword in award for keyword in ["품질", "안정", "테스트", "버그", "수호자", "지킴이", "머지"]):
                categories["🎯 품질 & 안정성"].append(award)
            # Special contribution awards
            elif any(keyword in award for keyword in ["문서", "리팩터링", "기능", "빅뱅", "미세", "아키텍트", "빌더", "건축가"]):
                categories["🎨 특별 기여"].append(award)
            # Top honors
            elif any(keyword in award for keyword in ["르네상스", "다재다능", "올라운더", "일관성의 왕", "균형"]):
                categories["👑 최고 영예"].append(award)
            # Default category
            else:
                categories["🎖️ 기본 성취"].append(award)

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
        lines = ["# GitHub Feedback Report", ""]
        lines.append(f"Repository: **{metrics.repo}**")
        lines.append(f"Period: **{metrics.months} months**")

        if metrics.since_date and metrics.until_date:
            since_str = metrics.since_date.strftime("%Y-%m-%d")
            until_str = metrics.until_date.strftime("%Y-%m-%d")
            lines.append(f"Analysis Period: **{since_str} ~ {until_str}**")

        lines.append("")
        lines.append("## Summary")

        for key, value in metrics.summary.items():
            display_value = (
                _format_metric_value(value) if isinstance(value, (int, float)) else str(value)
            )
            lines.append(f"- **{key.title()}**: {display_value}")
        lines.append("")

        return lines

    def _build_metrics_section(self, metrics: MetricSnapshot) -> List[str]:
        """Build metrics section."""
        lines = ["## Metrics", ""]
        for domain, domain_stats in metrics.stats.items():
            lines.append(f"### {domain.title()}")
            for stat_name, stat_value in domain_stats.items():
                formatted_value = (
                    _format_metric_value(stat_value)
                    if isinstance(stat_value, (int, float))
                    else str(stat_value)
                )
                lines.append(f"- {stat_name.replace('_', ' ').title()}: {formatted_value}")
            lines.append("")
        return lines

    def _build_highlights_section(self, metrics: MetricSnapshot) -> List[str]:
        """Build growth highlights section."""
        if not metrics.highlights:
            return []

        lines = ["## Growth Highlights"]
        for highlight in metrics.highlights:
            lines.append(f"- {highlight}")
        lines.append("")
        return lines

    def _build_spotlight_section(self, metrics: MetricSnapshot) -> List[str]:
        """Build spotlight examples section."""
        if not metrics.spotlight_examples:
            return []

        lines = ["## Spotlight Examples"]
        for category, entries in metrics.spotlight_examples.items():
            lines.append(f"### {category.replace('_', ' ').title()}")
            for entry in entries:
                lines.append(f"- {entry}")
            lines.append("")
        return lines

    def _build_year_in_review_section(self, metrics: MetricSnapshot) -> List[str]:
        """Build year in review section."""
        if not metrics.yearbook_story:
            return []

        lines = ["## Year in Review", ""]
        for paragraph in metrics.yearbook_story:
            lines.append(paragraph)
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

    def _build_evidence_section(self, metrics: MetricSnapshot) -> List[str]:
        """Build evidence section."""
        lines = ["## Evidence"]
        for domain, links in metrics.evidence.items():
            lines.append(f"### {domain.title()}")
            for link in links:
                lines.append(f"- {link}")
            lines.append("")
        return lines

    def _build_detailed_feedback_section(self, metrics: MetricSnapshot) -> List[str]:
        """Build detailed feedback section."""
        if not metrics.detailed_feedback:
            return []

        lines = ["## 상세 피드백", ""]
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

        return lines

    def _build_commit_feedback(self, cf) -> List[str]:
        """Build commit feedback subsection."""
        lines = ["### 커밋 메시지 품질"]
        lines.append(f"- 총 커밋: {cf.total_commits}")
        lines.append(f"- 좋은 메시지: {cf.good_messages}")
        lines.append(f"- 개선 필요: {cf.poor_messages}")

        if cf.suggestions:
            lines.append("")
            lines.append("**개선 제안:**")
            for suggestion in cf.suggestions:
                lines.append(f"- {suggestion}")

        if cf.examples_good:
            lines.append("")
            lines.append("**좋은 예시:**")
            for example in cf.examples_good:
                if isinstance(example, dict):
                    lines.append(f"- {example.get('message', '')} ({example.get('sha', '')})")
                else:
                    lines.append(f"- {example}")

        if cf.examples_poor:
            lines.append("")
            lines.append("**개선이 필요한 예시:**")
            for example in cf.examples_poor:
                if isinstance(example, dict):
                    lines.append(f"- {example.get('message', '')} ({example.get('sha', '')})")
                else:
                    lines.append(f"- {example}")
        lines.append("")
        return lines

    def _build_pr_title_feedback(self, pf) -> List[str]:
        """Build PR title feedback subsection."""
        lines = ["### PR 제목 품질"]
        lines.append(f"- 총 PR: {pf.total_prs}")
        lines.append(f"- 명확한 제목: {pf.clear_titles}")
        lines.append(f"- 모호한 제목: {pf.vague_titles}")

        if pf.suggestions:
            lines.append("")
            lines.append("**개선 제안:**")
            for suggestion in pf.suggestions:
                lines.append(f"- {suggestion}")

        if pf.examples_good:
            lines.append("")
            lines.append("**좋은 예시:**")
            for example in pf.examples_good:
                if isinstance(example, dict):
                    lines.append(f"- #{example.get('number', '')}: {example.get('title', '')}")
                else:
                    lines.append(f"- {example}")

        if pf.examples_poor:
            lines.append("")
            lines.append("**개선이 필요한 예시:**")
            for example in pf.examples_poor:
                if isinstance(example, dict):
                    lines.append(f"- #{example.get('number', '')}: {example.get('title', '')}")
                else:
                    lines.append(f"- {example}")
        lines.append("")
        return lines

    def _build_review_tone_feedback(self, rf) -> List[str]:
        """Build review tone feedback subsection."""
        lines = ["### 리뷰 톤 분석"]
        lines.append(f"- 총 리뷰: {rf.total_reviews}")
        lines.append(f"- 건설적인 리뷰: {rf.constructive_reviews}")
        lines.append(f"- 가혹한 리뷰: {rf.harsh_reviews}")
        lines.append(f"- 중립적인 리뷰: {rf.neutral_reviews}")

        if rf.suggestions:
            lines.append("")
            lines.append("**개선 제안:**")
            for suggestion in rf.suggestions:
                lines.append(f"- {suggestion}")

        if rf.examples_good:
            lines.append("")
            lines.append("**좋은 예시:**")
            for example in rf.examples_good:
                lines.append(f"- {example}")

        if rf.examples_improve:
            lines.append("")
            lines.append("**개선이 필요한 예시:**")
            for example in rf.examples_improve:
                lines.append(f"- {example}")
        lines.append("")
        return lines

    def _build_issue_feedback(self, isf) -> List[str]:
        """Build issue feedback subsection."""
        lines = ["### 이슈 품질"]
        lines.append(f"- 총 이슈: {isf.total_issues}")
        lines.append(f"- 잘 작성됨: {isf.well_described}")
        lines.append(f"- 개선 필요: {isf.poorly_described}")

        if isf.suggestions:
            lines.append("")
            lines.append("**개선 제안:**")
            for suggestion in isf.suggestions:
                lines.append(f"- {suggestion}")

        if isf.examples_good:
            lines.append("")
            lines.append("**좋은 예시:**")
            for example in isf.examples_good:
                if isinstance(example, dict):
                    lines.append(f"- #{example.get('number', '')}: {example.get('title', '')}")
                else:
                    lines.append(f"- {example}")

        if isf.examples_poor:
            lines.append("")
            lines.append("**개선이 필요한 예시:**")
            for example in isf.examples_poor:
                if isinstance(example, dict):
                    lines.append(f"- #{example.get('number', '')}: {example.get('title', '')}")
                else:
                    lines.append(f"- {example}")
        lines.append("")
        return lines

    def _build_monthly_trends_section(self, metrics: MetricSnapshot) -> List[str]:
        """Build monthly trends section."""
        if not metrics.monthly_trends:
            return []

        lines = ["## 📈 월별 활동 트렌드", ""]

        if metrics.monthly_insights and metrics.monthly_insights.insights:
            lines.append("### 트렌드 분석")
            lines.append("")
            for insight in metrics.monthly_insights.insights:
                lines.append(f"- {insight}")
            lines.append("")

        lines.append("### 월별 상세 데이터")
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
        return lines

    def _build_tech_stack_section(self, metrics: MetricSnapshot) -> List[str]:
        """Build tech stack section."""
        if not metrics.tech_stack:
            return []

        lines = ["## 💻 기술 스택 분석", ""]
        lines.append(f"**다양성 점수**: {metrics.tech_stack.diversity_score:.2f} (0-1 척도)")
        lines.append("")
        lines.append("**주요 사용 언어:**")
        for i, lang in enumerate(metrics.tech_stack.top_languages[:5], 1):
            count = metrics.tech_stack.languages.get(lang, 0)
            lines.append(f"{i}. {lang} ({count}개 파일)")
        lines.append("")
        return lines

    def _build_collaboration_section(self, metrics: MetricSnapshot) -> List[str]:
        """Build collaboration section."""
        if not metrics.collaboration:
            return []

        lines = ["## 🤝 협업 네트워크", ""]
        lines.append(f"- 받은 리뷰 수: **{metrics.collaboration.review_received_count}건**")
        lines.append(f"- 협업한 사람 수: **{metrics.collaboration.unique_collaborators}명**")
        lines.append("")

        if metrics.collaboration.top_reviewers:
            lines.append("**주요 리뷰어:**")
            for i, reviewer in enumerate(metrics.collaboration.top_reviewers, 1):
                count = metrics.collaboration.pr_reviewers.get(reviewer, 0)
                lines.append(f"{i}. @{reviewer} ({count}회)")
            lines.append("")
        return lines

    def _build_reflection_prompts_section(self, metrics: MetricSnapshot) -> List[str]:
        """Build reflection prompts section."""
        if not (metrics.reflection_prompts and metrics.reflection_prompts.questions):
            return []

        lines = ["## 🤔 회고 질문", ""]
        lines.append("스스로에게 물어보세요:")
        lines.append("")
        for i, question in enumerate(metrics.reflection_prompts.questions, 1):
            lines.append(f"{i}. {question}")
        lines.append("")
        return lines

    def _build_year_end_review_section(self, metrics: MetricSnapshot) -> List[str]:
        """Build year-end review section."""
        if not metrics.year_end_review:
            return []

        lines = ["## 🎯 연말 회고", ""]

        if metrics.year_end_review.proudest_moments:
            lines.append("### 자랑스러운 순간들")
            for moment in metrics.year_end_review.proudest_moments:
                lines.append(f"- {moment}")
            lines.append("")

        if metrics.year_end_review.biggest_challenges:
            lines.append("### 극복한 도전들")
            for challenge in metrics.year_end_review.biggest_challenges:
                lines.append(f"- {challenge}")
            lines.append("")

        if metrics.year_end_review.lessons_learned:
            lines.append("### 배운 교훈들")
            for lesson in metrics.year_end_review.lessons_learned:
                lines.append(f"- {lesson}")
            lines.append("")

        if metrics.year_end_review.next_year_goals:
            lines.append("### 내년 목표")
            for goal in metrics.year_end_review.next_year_goals:
                lines.append(f"- {goal}")
            lines.append("")

        return lines

    def generate_markdown(self, metrics: MetricSnapshot) -> Path:
        """Create a markdown report for the provided metrics."""
        self.ensure_structure()
        report_path = self.output_dir / "report.md"

        console.log("Writing markdown report", f"path={report_path}")

        # Build all sections
        sections = [
            self._build_header_and_summary(metrics),
            self._build_metrics_section(metrics),
            self._build_highlights_section(metrics),
            self._build_spotlight_section(metrics),
            self._build_year_in_review_section(metrics),
            self._build_awards_section(metrics),
            self._build_evidence_section(metrics),
            self._build_detailed_feedback_section(metrics),
            self._build_monthly_trends_section(metrics),
            self._build_tech_stack_section(metrics),
            self._build_collaboration_section(metrics),
            self._build_reflection_prompts_section(metrics),
            self._build_year_end_review_section(metrics),
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

