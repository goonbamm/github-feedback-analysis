"""연말 결산 보고서 생성 - 메인 orchestrator."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import List

from ..console import Console
from ..game_elements import get_animation_styles
from .models import RepositoryAnalysis
from .sections.character_stats import generate_character_stats
from .sections.communication_section import generate_communication_skills_section
from .sections.executive_summary import generate_executive_summary
from .sections.goals_section import generate_footer, generate_goals_section
from .sections.header_section import generate_header
from .sections.repository_breakdown import generate_repository_breakdown
from .sections.tech_stack_section import generate_tech_stack_analysis

console = Console()


class YearInReviewReporter:
    """Generate comprehensive year-in-review reports."""

    def __init__(self, output_dir: Path = Path("reports/year-in-review")) -> None:
        from ..utils import FileSystemManager

        self.output_dir = output_dir
        FileSystemManager.ensure_directory(self.output_dir)

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
        sorted_tech_stack = self._aggregate_tech_stack(repository_analyses)

        # Add font styles and animations at the beginning
        font_styles = [
            '<style>',
            '  @import url("https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&display=swap");',
            '  * {',
            '    font-family: "Noto Sans KR", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;',
            '  }',
            '</style>',
            ''
        ]

        # Add animation styles
        animation_styles = get_animation_styles()

        # Generate report with game character theme
        lines = font_styles[:]
        lines.append(animation_styles)
        lines.extend(generate_header(year, username, total_repos, total_prs, total_commits))
        lines.extend(generate_character_stats(year, total_repos, total_prs, total_commits, repository_analyses))
        lines.extend(generate_executive_summary(repository_analyses, sorted_tech_stack))
        lines.extend(generate_communication_skills_section(repository_analyses))
        lines.extend(generate_tech_stack_analysis(sorted_tech_stack))
        lines.extend(generate_repository_breakdown(repository_analyses, self.output_dir))
        lines.extend(generate_goals_section(repository_analyses, year))
        lines.extend(generate_footer())

        # Save report
        report_path = self.output_dir / f"year_{year}_in_review.md"
        report_path.write_text("\n".join(lines), encoding="utf-8")

        console.log(f"✅ Year-in-review report saved: {report_path}")
        return report_path

    def _aggregate_tech_stack(
        self, repository_analyses: List[RepositoryAnalysis]
    ) -> List[tuple]:
        """Aggregate tech stack across all repositories."""
        combined_tech_stack = defaultdict(int)
        repos_with_tech_stack = 0

        for repo in repository_analyses:
            if repo.tech_stack:
                repos_with_tech_stack += 1
                console.log(f"[dim]  {repo.full_name}: {len(repo.tech_stack)} technologies[/]")
                for lang, count in repo.tech_stack.items():
                    combined_tech_stack[lang] += count
            else:
                console.log(f"[warning]  {repo.full_name}: No tech stack data[/]")

        # Sort tech stack by usage
        sorted_tech_stack = sorted(
            combined_tech_stack.items(), key=lambda x: x[1], reverse=True
        )

        total_repos = len(repository_analyses)
        console.log(
            f"[dim]Tech stack aggregation: {repos_with_tech_stack}/{total_repos} repos with data, "
            f"{len(sorted_tech_stack)} total technologies[/]"
        )

        return sorted_tech_stack


__all__ = ["YearInReviewReporter", "RepositoryAnalysis"]
