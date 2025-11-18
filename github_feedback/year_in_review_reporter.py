"""Generate comprehensive year-in-review reports aggregating multiple repositories."""
from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .console import Console

console = Console()


@dataclass
class RepositoryAnalysis:
    """Individual repository analysis data."""

    full_name: str
    pr_count: int
    commit_count: int
    year_commits: int
    integrated_report_path: Optional[Path] = None
    personal_dev_path: Optional[Path] = None
    strengths: List[Dict[str, Any]] = None
    improvements: List[Dict[str, Any]] = None
    growth_indicators: List[Dict[str, Any]] = None
    tech_stack: Dict[str, int] = None

    def __post_init__(self):
        if self.strengths is None:
            self.strengths = []
        if self.improvements is None:
            self.improvements = []
        if self.growth_indicators is None:
            self.growth_indicators = []
        if self.tech_stack is None:
            self.tech_stack = {}


class YearInReviewReporter:
    """Generate comprehensive year-in-review reports."""

    def __init__(self, output_dir: Path = Path("reports/year-in-review")) -> None:
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def create_year_in_review_report(
        self,
        year: int,
        username: str,
        repository_analyses: List[RepositoryAnalysis],
    ) -> Path:
        """Create comprehensive year-in-review report.

        Args:
            year: Year being reviewed
            username: GitHub username
            repository_analyses: List of repository analysis data

        Returns:
            Path to the generated report
        """
        if not repository_analyses:
            raise ValueError("No repository analyses provided")

        # Aggregate statistics
        total_prs = sum(r.pr_count for r in repository_analyses)
        total_commits = sum(r.year_commits for r in repository_analyses)
        total_repos = len(repository_analyses)

        # Aggregate tech stack
        combined_tech_stack = defaultdict(int)
        for repo in repository_analyses:
            for lang, count in repo.tech_stack.items():
                combined_tech_stack[lang] += count

        # Sort tech stack by usage
        sorted_tech_stack = sorted(
            combined_tech_stack.items(), key=lambda x: x[1], reverse=True
        )

        # Generate report
        lines = self._generate_header(year, username, total_repos, total_prs, total_commits)
        lines.extend(self._generate_executive_summary(repository_analyses, sorted_tech_stack))
        lines.extend(self._generate_repository_breakdown(repository_analyses))
        lines.extend(self._generate_tech_stack_analysis(sorted_tech_stack))
        lines.extend(self._generate_aggregated_insights(repository_analyses))
        lines.extend(self._generate_goals_section(repository_analyses, year))
        lines.extend(self._generate_footer())

        # Save report
        report_path = self.output_dir / f"year_{year}_in_review.md"
        report_path.write_text("\n".join(lines), encoding="utf-8")

        console.log(f"✅ Year-in-review report saved: {report_path}")
        return report_path

    def _generate_header(
        self, year: int, username: str, total_repos: int, total_prs: int, total_commits: int
    ) -> List[str]:
        """Generate report header."""
        lines = [
            f"# 🎊 {year} Year in Review",
            "",
            f"> Comprehensive analysis of @{username}'s contributions in {year}",
            "",
            f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "---",
            "",
            "## 🎯 Executive Summary",
            "",
            f"In {year}, you made significant contributions across **{total_repos} repositories**, creating **{total_prs} pull requests** and committing **{total_commits} times**. This report synthesizes your growth, achievements, and areas for future development.",
            "",
            "### Key Metrics at a Glance",
            "",
            "| Metric | Value |",
            "|--------|-------|",
            f"| 📦 **Repositories** | {total_repos} |",
            f"| 🔀 **Pull Requests** | {total_prs} |",
            f"| 💾 **Commits** | {total_commits} |",
            f"| 📊 **Average PRs per Repo** | {total_prs // total_repos if total_repos > 0 else 0} |",
            "",
            "---",
            "",
        ]
        return lines

    def _generate_executive_summary(
        self, repository_analyses: List[RepositoryAnalysis], tech_stack: List[tuple]
    ) -> List[str]:
        """Generate executive summary with top highlights."""
        lines = [
            "## 🏆 Top Highlights",
            "",
        ]

        # Most active repository
        most_active = max(repository_analyses, key=lambda r: r.pr_count)
        lines.append(f"- **Most Active Repository**: {most_active.full_name} ({most_active.pr_count} PRs)")

        # Most committed repository
        most_commits = max(repository_analyses, key=lambda r: r.year_commits)
        if most_commits.full_name != most_active.full_name:
            lines.append(
                f"- **Most Committed Repository**: {most_commits.full_name} ({most_commits.year_commits} commits)"
            )

        # Primary technologies
        if tech_stack:
            top_3_tech = [tech[0] for tech in tech_stack[:3]]
            lines.append(f"- **Primary Technologies**: {', '.join(top_3_tech)}")

        lines.extend(["", "---", ""])
        return lines

    def _generate_repository_breakdown(
        self, repository_analyses: List[RepositoryAnalysis]
    ) -> List[str]:
        """Generate per-repository breakdown."""
        lines = [
            "## 📊 Repository Breakdown",
            "",
            "> Detailed analysis of each repository you contributed to",
            "",
        ]

        for idx, repo in enumerate(repository_analyses, 1):
            lines.append(f"### {idx}. {repo.full_name}")
            lines.append("")
            lines.append("| Metric | Value |")
            lines.append("|--------|-------|")
            lines.append(f"| Pull Requests | {repo.pr_count} |")
            lines.append(f"| Commits ({repo.year_commits} in year) | {repo.commit_count} total |")

            if repo.tech_stack:
                top_langs = sorted(repo.tech_stack.items(), key=lambda x: x[1], reverse=True)[:3]
                langs_str = ", ".join([f"{lang} ({count})" for lang, count in top_langs])
                lines.append(f"| Top Languages | {langs_str} |")

            lines.append("")

            # Link to detailed report
            if repo.integrated_report_path:
                lines.append(f"📄 **[View Detailed Report]({repo.integrated_report_path.relative_to(self.output_dir.parent)})**")
                lines.append("")

            # Key insights from personal development
            if repo.strengths:
                lines.append("**✨ Key Strengths:**")
                for strength in repo.strengths[:2]:  # Top 2 strengths
                    category = strength.get("category", "")
                    desc = strength.get("description", "")
                    lines.append(f"- **{category}**: {desc}")
                lines.append("")

            if repo.improvements:
                lines.append("**💡 Areas for Growth:**")
                for improvement in repo.improvements[:2]:  # Top 2 improvements
                    category = improvement.get("category", "")
                    desc = improvement.get("description", "")
                    lines.append(f"- **{category}**: {desc}")
                lines.append("")

            lines.append("---")
            lines.append("")

        return lines

    def _generate_tech_stack_analysis(self, tech_stack: List[tuple]) -> List[str]:
        """Generate technology stack analysis."""
        lines = [
            "## 💻 Technology Stack Evolution",
            "",
            "> Languages and frameworks you worked with this year",
            "",
        ]

        if not tech_stack:
            lines.append("_No technology data available._")
            lines.extend(["", "---", ""])
            return lines

        total_changes = sum(count for _, count in tech_stack)

        lines.append("| Language/Framework | Usage | Percentage |")
        lines.append("|-------------------|-------|------------|")

        for lang, count in tech_stack[:10]:  # Top 10
            percentage = (count / total_changes * 100) if total_changes > 0 else 0
            bar = "█" * int(percentage / 5)  # Visual bar (each █ = 5%)
            lines.append(f"| {lang} | {count} | {percentage:.1f}% {bar} |")

        lines.extend(["", "---", ""])
        return lines

    def _generate_aggregated_insights(
        self, repository_analyses: List[RepositoryAnalysis]
    ) -> List[str]:
        """Generate aggregated insights across all repositories."""
        lines = [
            "## 🌟 Aggregated Insights",
            "",
            "> Cross-repository patterns and growth trends",
            "",
        ]

        # Collect all strengths and improvements
        all_strengths = defaultdict(int)
        all_improvements = defaultdict(int)

        for repo in repository_analyses:
            for strength in repo.strengths:
                category = strength.get("category", "Other")
                all_strengths[category] += 1

            for improvement in repo.improvements:
                category = improvement.get("category", "Other")
                all_improvements[category] += 1

        # Top recurring strengths
        if all_strengths:
            lines.append("### ✅ Recurring Strengths")
            lines.append("")
            sorted_strengths = sorted(all_strengths.items(), key=lambda x: x[1], reverse=True)
            for category, count in sorted_strengths[:5]:
                lines.append(f"- **{category}** (appeared in {count} repositories)")
            lines.append("")

        # Top recurring improvement areas
        if all_improvements:
            lines.append("### 🔧 Recurring Improvement Areas")
            lines.append("")
            sorted_improvements = sorted(all_improvements.items(), key=lambda x: x[1], reverse=True)
            for category, count in sorted_improvements[:5]:
                lines.append(f"- **{category}** (appeared in {count} repositories)")
            lines.append("")

        # Growth indicators
        lines.append("### 📈 Growth Indicators")
        lines.append("")

        repos_with_growth = [r for r in repository_analyses if r.growth_indicators]
        if repos_with_growth:
            lines.append(f"- Showed measurable growth in **{len(repos_with_growth)} out of {len(repository_analyses)} repositories**")

            # Sample growth examples
            for repo in repos_with_growth[:3]:
                if repo.growth_indicators:
                    indicator = repo.growth_indicators[0]
                    aspect = indicator.get("aspect", "")
                    summary = indicator.get("progress_summary", "")
                    lines.append(f"- **{repo.full_name}**: {aspect} - {summary}")
        else:
            lines.append("- _No specific growth indicators identified across repositories_")

        lines.extend(["", "---", ""])
        return lines

    def _generate_goals_section(
        self, repository_analyses: List[RepositoryAnalysis], year: int
    ) -> List[str]:
        """Generate goals and recommendations for next year."""
        lines = [
            f"## 🎯 Goals for {year + 1}",
            "",
            "> Based on your {year} performance, here are recommended focus areas",
            "",
        ]

        # Collect all improvement suggestions
        all_suggestions = []
        for repo in repository_analyses:
            for improvement in repo.improvements:
                suggestions = improvement.get("suggestions", [])
                all_suggestions.extend(suggestions)

        # Deduplicate and limit
        unique_suggestions = list(dict.fromkeys(all_suggestions))[:5]

        if unique_suggestions:
            lines.append("### 💡 Recommended Focus Areas")
            lines.append("")
            for idx, suggestion in enumerate(unique_suggestions, 1):
                lines.append(f"{idx}. {suggestion}")
            lines.append("")

        lines.append("### 🚀 Action Items")
        lines.append("")
        lines.append("- [ ] Review detailed feedback for each repository")
        lines.append("- [ ] Set specific, measurable goals for top improvement areas")
        lines.append("- [ ] Explore new technologies or deepen expertise in current stack")
        lines.append("- [ ] Increase collaboration and code review participation")
        lines.append(f"- [ ] Track progress quarterly throughout {year + 1}")
        lines.append("")

        lines.append("---")
        lines.append("")
        return lines

    def _generate_footer(self) -> List[str]:
        """Generate report footer."""
        return [
            "## 🎉 Closing Thoughts",
            "",
            "Every commit, PR, and review contributes to your growth as a developer. ",
            "Use this report to celebrate your achievements and plan for continued improvement.",
            "",
            "**Remember**: Consistent progress beats occasional perfection. Keep shipping! 🚀",
            "",
            "---",
            "",
            "<div align=\"center\">",
            "",
            "*Generated by GitHub Feedback Analysis Tool*",
            "",
            "</div>",
        ]


__all__ = ["YearInReviewReporter", "RepositoryAnalysis"]
