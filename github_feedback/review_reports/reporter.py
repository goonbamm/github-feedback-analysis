"""Review reporter - Main orchestrator for generating review reports."""

from __future__ import annotations

import json
from pathlib import Path
from typing import List

from ..core.console import Console
from ..game_elements import GameRenderer
from ..llm.client import LLMClient
from ..prompts import get_team_report_system_prompt, get_team_report_user_prompt
from .analysis import PersonalDevelopmentAnalyzer
from .data_loader import ReviewDataLoader, StoredReview
from .sections import (
    render_character_stats,
    render_code_changes_visualization,
    render_personal_development,
    render_pr_activity_timeline,
    render_statistics_dashboard,
)

console = Console()


class ReviewReporter:
    """Build integrated Korean reports from individual pull request reviews."""

    def __init__(self, *, output_dir: Path = Path("reports/reviews"), llm: LLMClient | None = None) -> None:
        self.output_dir = output_dir
        self.llm = llm
        self.data_loader = ReviewDataLoader(output_dir)
        self.analyzer = PersonalDevelopmentAnalyzer(llm)

    def create_integrated_report(self, repo: str) -> Path:
        """Create or refresh the integrated review report for a repository.

        The report structure is consistent regardless of LLM availability:
        1. Header with repository info
        2. Character stats (RPG-style visualization)
        3. Personal development analysis (strengths, growth, improvements)
        4. Team report (if LLM available) or statistics
        5. PR activity visualizations
        6. PR list and closing message
        """
        repo_input = repo.strip()
        if not repo_input:
            raise ValueError("Repository cannot be empty")

        reviews = self.data_loader.load_reviews(repo_input)
        if not reviews:
            raise ValueError("No review summaries found for the given repository")

        # Generate integrated report with all sections
        console.log("통합 보고서 생성 중... (캐릭터 스탯 + 개인 피드백 + 팀 분석)")
        report_text = self._generate_report_text(repo_input, reviews)

        # Save report
        from ..core.utils import FileSystemManager

        repo_dir = self.data_loader._repo_dir(repo_input)
        FileSystemManager.ensure_directory(repo_dir)
        report_path = repo_dir / "integrated_report.md"
        report_path.write_text(report_text, encoding="utf-8")

        # Also save personal development analysis as JSON for programmatic access
        console.log("개인 성장 분석 JSON 저장 중...")
        personal_dev = self.analyzer.analyze(repo_input, reviews)
        personal_dev_path = repo_dir / "personal_development.json"
        personal_dev_path.write_text(
            json.dumps(personal_dev.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        console.log(f"✅ 통합 보고서 완성: {report_path}")
        console.log(f"✅ 개인 성장 분석: {personal_dev_path}")
        return report_path

    def _generate_report_text(self, repo: str, reviews: List[StoredReview]) -> str:
        """Generate integrated report with consistent structure regardless of LLM availability.

        Structure:
        1. Header and intro
        2. Character stats (RPG-style)
        3. Personal development analysis (strengths, growth, improvements)
        4. Team report (if LLM available) or statistics
        5. PR activity visualizations
        6. PR list and closing
        """
        lines: List[str] = []

        # Add font styles at the beginning
        lines.append("<style>")
        lines.append(
            '  @import url("https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&display=swap");'
        )
        lines.append("  * {")
        lines.append(
            '    font-family: "Noto Sans KR", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;'
        )
        lines.append("  }")
        lines.append("</style>")
        lines.append("")

        # ============ 1. Header ============
        lines.append("# 🎯 개발자 성장 리포트")
        lines.append("")
        lines.append(f"**저장소**: {repo}")
        lines.append(f"**분석 기간**: 총 {len(reviews)}개의 PR")
        lines.append("")
        lines.append(
            "> 💡 **보고서 활용 팁**: 스탯을 먼저 확인하고, 장점과 성장한 점에서 자신감을 얻은 후, 보완점에서 다음 목표를 찾아보세요!"
        )
        lines.append("")
        lines.append("---")
        lines.append("")

        # ============ 2. Character Stats (RPG-style) ============
        lines.extend(render_character_stats(reviews))

        # ============ 3. Personal Development Analysis ============
        personal_dev = self.analyzer.analyze(repo, reviews)
        lines.extend(render_personal_development(personal_dev, reviews))

        # ============ 4. Team Report (if LLM available) ============
        if self.llm:
            try:
                context = self._build_prompt_context(repo, reviews)
                messages = [
                    {
                        "role": "system",
                        "content": get_team_report_system_prompt(),
                    },
                    {
                        "role": "user",
                        "content": get_team_report_user_prompt(context),
                    },
                ]
                # Increased temperature from 0.4 to 0.5 for better response quality
                # Increased max_retries to 5 for more robust analysis
                team_report = self.llm.complete(messages, temperature=0.5, max_retries=5)
                if team_report.strip():
                    lines.append("---")
                    lines.append("")
                    lines.append(team_report.strip())
                    lines.append("")
                    lines.append("---")
                    lines.append("")
            except Exception as exc:  # pragma: no cover
                console.log("LLM 팀 보고서 생성 실패, 기본 통계로 대체", str(exc))
                lines.extend(render_statistics_dashboard(reviews))
        else:
            lines.extend(render_statistics_dashboard(reviews))

        # ============ 5. PR Activity Visualizations ============
        lines.extend(render_pr_activity_timeline(reviews))
        lines.extend(render_code_changes_visualization(reviews))

        # ============ 6. PR List and Closing ============
        lines.append("## 📝 전체 PR 목록")
        lines.append("")
        lines.append("> 분석에 포함된 모든 PR 목록입니다")
        lines.append("")

        # Build table data
        headers = ["#", "PR", "제목", "날짜", "링크"]
        rows = []
        for i, review in enumerate(reviews, 1):
            date_str = review.created_at.strftime("%Y-%m-%d")
            title_short = review.title[:50] + "..." if len(review.title) > 50 else review.title
            link = f"[보기]({review.html_url})" if review.html_url else "-"
            rows.append([str(i), f"#{review.number}", title_short, date_str, link])

        # Render as HTML table
        lines.extend(GameRenderer.render_html_table(headers=headers, rows=rows, title="", description="", striped=True))

        lines.append("---")
        lines.append("")

        lines.append("## 🎉 마무리")
        lines.append("")
        lines.append(
            f"총 **{len(reviews)}개의 PR**을 통해 꾸준히 성장하고 있습니다! 🚀\n\n"
            "이 보고서가 여러분의 강점을 확인하고, 다음 성장 목표를 설정하는 데 도움이 되었기를 바랍니다. "
            "기억하세요: **모든 PR은 성장의 기회**입니다! 💪\n\n"
            "다음 리포트에서 더 멋진 성장을 기대합니다! 🌟"
        )
        lines.append("")

        return "\n".join(lines).strip()

    def _build_prompt_context(self, repo: str, reviews: List[StoredReview]) -> str:
        """Build context string for team report prompt."""
        lines: List[str] = []
        lines.append(f"Repository: {repo}")
        lines.append(f"총 리뷰 PR 수: {len(reviews)}")
        lines.append("")
        lines.append("Pull Request 요약:")

        for review in reviews:
            code_metrics = f"+{review.additions}/-{review.deletions}, {review.changed_files}개 파일 변경"
            lines.append(
                f"- PR #{review.number} {review.title} (작성자: {review.author}, 생성일: {review.created_at.date()}, 코드 변경: {code_metrics})"
            )
            if review.html_url:
                lines.append(f"  URL: {review.html_url}")
            if review.overview:
                lines.append(f"  Overview: {review.overview}")
            lines.append("")

        return "\n".join(lines).strip()


__all__ = ["ReviewReporter"]
