"""Command line interface for the GitHub feedback toolkit."""

from __future__ import annotations

import json
import logging
import os
import sys
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Annotated, Any, Callable, Dict, List, Optional, Tuple

import requests
import typer

try:  # pragma: no cover - optional rich dependency
    from rich import box
    from rich.align import Align
    from rich.columns import Columns
    from rich.console import Group
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeRemainingColumn
    from rich.rule import Rule
    from rich.table import Table
    from rich.text import Text
except ModuleNotFoundError:  # pragma: no cover - fallback when rich is missing
    Align = None
    Columns = None
    Group = None
    Panel = None
    Progress = None
    Rule = None
    Table = None
    Text = None
    box = None

from .analyzer import Analyzer
from .collector import Collector
from .config import Config
from .console import Console
from .constants import (
    COLLECTION_LIMITS,
    DAYS_PER_MONTH_APPROX,
    DAYS_PER_YEAR,
    ERROR_MESSAGES,
    INFO_MESSAGES,
    PARALLEL_CONFIG,
    SPINNERS,
    SUCCESS_MESSAGES,
    TABLE_CONFIG,
    TaskType,
)
from .exceptions import (
    CollectionError,
    CollectionTimeoutError,
    LLMAnalysisError,
    LLMTimeoutError,
)
from .llm import LLMClient
from .models import (
    AnalysisFilters,
    AnalysisStatus,
    DetailedFeedbackSnapshot,
    MetricSnapshot,
)
from .reporter import Reporter
from .repository_display import create_repository_table, format_relative_date
from .review_reporter import ReviewReporter
from .reviewer import Reviewer
from .utils import validate_pat_format, validate_url, validate_repo_format, validate_months

# Import refactored CLI modules
from . import cli_helpers
from . import cli_repository
from . import cli_metrics
from . import cli_data_collection

app = typer.Typer(help="Analyze GitHub repositories and generate feedback reports.")
config_app = typer.Typer(help="Manage configuration settings")
app.add_typer(config_app, name="config")

console = Console()
logger = logging.getLogger(__name__)


@app.command()
def init(
    pat: Optional[str] = typer.Option(
        None,
        "--pat",
        help="GitHub Personal Access Token (requires 'repo' scope for private repos)",
        hide_input=True,
    ),
    months: int = typer.Option(12, "--months", help="Default analysis window in months"),
    enterprise_host: Optional[str] = typer.Option(
        None,
        "--enterprise-host",
        help=(
            "Base URL of your GitHub Enterprise host (e.g. https://github.example.com). "
            "When provided, API, GraphQL, and web URLs are derived automatically."
        ),
    ),
    llm_endpoint: Optional[str] = typer.Option(
        None,
        "--llm-endpoint",
        help="LLM endpoint URL (e.g. https://api.openai.com/v1/chat/completions)",
    ),
    llm_model: Optional[str] = typer.Option(
        None,
        "--llm-model",
        help="Model identifier for the LLM",
    ),
    test_connection: bool = typer.Option(
        True,
        "--test/--no-test",
        help="Test LLM connection after configuration",
    ),
) -> None:
    """Initialize configuration and store credentials securely.

    This command sets up your GitHub access token, LLM endpoint, and other
    configuration options. Run this once before using other commands.

    Interactive mode: Run without options to be prompted for each value.
    Non-interactive mode: Provide all required options for scripting.
    """

    # Determine if we're in interactive mode
    is_interactive = sys.stdin.isatty()

    # Prompt for missing required values only in interactive mode
    with cli_helpers.handle_user_interruption("Configuration cancelled by user."):
        if pat is None:
            if is_interactive:
                pat = typer.prompt("GitHub Personal Access Token", hide_input=True)
            else:
                console.print("[danger]Error:[/] --pat is required in non-interactive mode")
                raise typer.Exit(code=1)

        if llm_endpoint is None:
            if is_interactive:
                llm_endpoint = typer.prompt("LLM API endpoint (OpenAI-compatible format)")
            else:
                console.print("[danger]Error:[/] --llm-endpoint is required in non-interactive mode")
                raise typer.Exit(code=1)

        if llm_model is None:
            if is_interactive:
                llm_model = typer.prompt("LLM model name (e.g. gpt-4, claude-3-5-sonnet-20241022)")
            else:
                console.print("[danger]Error:[/] --llm-model is required in non-interactive mode")
                raise typer.Exit(code=1)

        # Enterprise host selection with interactive menu
        should_save_host = False
        if enterprise_host is None and is_interactive:
            # Load config to get custom hosts
            temp_config = Config.load()
            result = cli_repository.select_enterprise_host_interactive(temp_config.server.custom_enterprise_hosts)
            if result is None:
                # User cancelled
                console.print("\n[warning]Configuration cancelled by user.[/]")
                raise typer.Exit(code=0)
            enterprise_host, should_save_host = result

    # Validate inputs
    try:
        validate_pat_format(pat)
        validate_months(months)
        validate_url(llm_endpoint, "LLM endpoint")
    except ValueError as exc:
        console.print_validation_error(str(exc))
        raise typer.Exit(code=1) from exc

    host_input = (enterprise_host or "").strip()
    if host_input:
        try:
            # Add scheme if missing
            if not host_input.startswith(("http://", "https://")):
                host_input = f"https://{host_input}"
            validate_url(host_input, "Enterprise host")
            host = host_input.rstrip("/")
        except ValueError as exc:
            console.print_validation_error(str(exc))
            raise typer.Exit(code=1) from exc

        api_url = f"{host}/api/v3"
        graphql_url = f"{host}/api/graphql"
        web_url = host
    else:
        api_url = "https://api.github.com"
        graphql_url = "https://api.github.com/graphql"
        web_url = "https://github.com"

    config = Config.load()
    config.update_auth(pat)
    config.server.api_url = api_url
    config.server.graphql_url = graphql_url
    config.server.web_url = web_url
    config.llm.endpoint = llm_endpoint
    config.llm.model = llm_model
    config.defaults.months = months

    # Save custom enterprise host if requested
    if should_save_host and host_input and host_input not in config.server.custom_enterprise_hosts:
        config.server.custom_enterprise_hosts.append(host_input)
        console.print(f"[success]✓ Saved '{host_input}' to your custom host list[/]")

    # Test LLM connection if requested
    if test_connection:
        console.print()
        with console.status("[accent]Testing LLM connection...", spinner="dots"):
            try:
                from .llm import LLMClient
                test_client = LLMClient(
                    endpoint=llm_endpoint,
                    model=llm_model,
                    timeout=10,
                )
                test_client.test_connection()
                console.print("[success]✓ LLM connection successful[/]")
            except KeyboardInterrupt:
                console.print("\n[warning]Configuration cancelled by user.[/]")
                raise typer.Exit(code=0)
            except (requests.RequestException, ValueError, ConnectionError) as exc:
                console.print(f"[warning]⚠ LLM connection test failed: {exc}[/]")
                with cli_helpers.handle_user_interruption("Configuration cancelled by user."):
                    if is_interactive and not typer.confirm("Save configuration anyway?", default=True):
                        console.print("[info]Configuration not saved[/]")
                        raise typer.Exit(code=1)

    config.dump()
    console.print("[success]✓ Configuration saved successfully[/]")
    console.print("[success]✓ GitHub token stored securely in system keyring[/]")
    console.print()
    _print_config_summary()


def _generate_artifacts(
    metrics: MetricSnapshot,
    reporter: Reporter,
    output_dir: Path,
    metrics_payload: dict,
    save_intermediate_report: bool = True,
) -> tuple[List[tuple[str, Path]], Optional[str]]:
    """Generate all report artifacts and return brief report content in memory.

    Args:
        metrics: Metrics snapshot to generate reports from
        reporter: Reporter instance
        output_dir: Output directory for artifacts
        metrics_payload: Metrics data for serialization
        save_intermediate_report: If True, generates brief report content in memory for integration.
                                  If False, skips brief report generation.

    Returns:
        Tuple of (artifacts, brief_content):
            - artifacts: List of (label, path) tuples for generated artifacts
            - brief_content: Markdown content for brief report (None if not generated)
    """
    artifacts = []

    # Save metrics
    metrics_path = cli_metrics.persist_metrics(output_dir=output_dir, metrics_data=metrics_payload)
    artifacts.append(("Metrics snapshot", metrics_path))

    # Generate markdown report content in memory (no _internal folder needed)
    brief_content = None
    if save_intermediate_report:
        # Generate content in memory without creating files
        brief_content = reporter.generate_markdown_content(metrics)
    else:
        markdown_path = reporter.generate_markdown(metrics)
        artifacts.append(("Markdown report", markdown_path))

    return artifacts, brief_content


def _run_feedback_analysis(
    config: Config,
    repo_input: str,
    output_dir: Path,
) -> tuple[Path | None, list[tuple[int, Path, Path, Path]]]:
    """Run feedback analysis for all PRs authored by the authenticated user.

    Args:
        config: Configuration object
        repo_input: Repository name in owner/repo format
        output_dir: Output directory for review artifacts

    Returns:
        Tuple of (integrated_report_path, pr_results)
        where pr_results is a list of (pr_number, artefact_path, summary_path, markdown_path)
    """
    try:
        collector = Collector(config)
    except ValueError as exc:
        console.print_error(exc)
        return None, []

    llm_client = LLMClient(
        endpoint=config.llm.endpoint,
        model=config.llm.model,
        timeout=config.llm.timeout,
        max_files_in_prompt=config.llm.max_files_in_prompt,
        max_files_with_patch_snippets=config.llm.max_files_with_patch_snippets,
        web_url=config.server.web_url,
    )

    reviews_dir = output_dir / "reviews"
    reviewer = Reviewer(collector=collector, llm=llm_client, output_dir=reviews_dir)

    # Get authenticated user
    with console.status("[accent]Retrieving authenticated user...", spinner="dots"):
        try:
            author = collector.get_authenticated_user()
        except (ValueError, PermissionError) as exc:
            console.print(f"[error]Failed to get authenticated user: {exc}[/]")
            return None, []

    # Find user's PRs
    with console.status("[accent]Finding your pull requests...", spinner="dots"):
        numbers = collector.list_authored_pull_requests(
            repo=repo_input,
            author=author,
            state="all",
        )

    if not numbers:
        console.print(
            f"[warning]No pull requests found authored by '{author}' in {repo_input}.[/]"
        )
        return None, []

    pr_numbers = sorted(set(numbers))
    total_prs = len(pr_numbers)

    # Generate PR reviews in parallel
    console.print(f"[info]Analyzing {total_prs} PRs in parallel...[/]")

    review_tasks = {
        f"pr_{pr_number}": (
            reviewer.review_pull_request,
            (repo_input, pr_number),
            f"PR #{pr_number}"
        )
        for pr_number in pr_numbers
    }

    review_results = cli_helpers.run_parallel_tasks(
        review_tasks,
        PARALLEL_CONFIG['max_workers_pr_review'],
        PARALLEL_CONFIG['pr_review_timeout'],
        task_type="analysis"
    )

    # Collect results
    results = []
    for pr_number in pr_numbers:
        key = f"pr_{pr_number}"
        if key in review_results and review_results[key] is not None:
            artefact_path, summary_path, markdown_path = review_results[key]
            results.append((pr_number, artefact_path, summary_path, markdown_path))
        else:
            console.print(f"[warning]⚠ PR #{pr_number} review failed or timed out[/]", style="warning")

    # Generate integrated report
    output_dir_resolved = cli_helpers.resolve_output_dir(output_dir)
    reviews_dir = output_dir_resolved / "reviews"
    review_reporter = ReviewReporter(
        output_dir=reviews_dir,
        llm=llm_client,
    )

    try:
        with console.status("[accent]Creating integrated report...", spinner="dots"):
            report_path = review_reporter.create_integrated_report(repo_input)
    except ValueError as exc:
        console.print(f"[warning]{exc}[/]")
        return None, results

    return report_path, results


def _generate_final_summary_table(personal_dev_path: Path) -> str:
    """Generate final summary table with strengths, improvements, and growth.

    Args:
        personal_dev_path: Path to personal_development.json file

    Returns:
        Markdown formatted final summary section with tables
    """
    import json

    # Try to load personal development data
    try:
        with open(personal_dev_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        # If file doesn't exist or can't be read, return empty summary
        return "## 📋 종합 피드백\n\n개인 성장 분석 데이터를 찾을 수 없습니다."

    # Extract top 3 strengths, top 2 improvements, top 3 growth indicators
    strengths = data.get("strengths", [])[:3]
    improvements = data.get("improvement_areas", [])[:2]
    growth = data.get("growth_indicators", [])[:3]

    # Build summary section
    lines = ["## 📋 종합 피드백", ""]

    # Strengths table
    if strengths:
        lines.append("### ✨ 주요 장점")
        lines.append("")
        lines.append("| 장점 | 근거 |")
        lines.append("|------|------|")
        for strength in strengths:
            category = strength.get("category", "기타")
            description = strength.get("description", "")
            evidence = strength.get("evidence", [])
            evidence_text = "<br>".join([f"• {e}" for e in evidence]) if evidence else "근거 없음"
            lines.append(f"| **{category}**: {description} | {evidence_text} |")
        lines.append("")

    # Improvements table
    if improvements:
        lines.append("### 💡 보완점")
        lines.append("")
        lines.append("| 보완점 | 근거 |")
        lines.append("|--------|------|")
        for improvement in improvements:
            category = improvement.get("category", "기타")
            description = improvement.get("description", "")
            evidence = improvement.get("evidence", [])
            evidence_text = "<br>".join([f"• {e}" for e in evidence]) if evidence else "근거 없음"
            lines.append(f"| **{category}**: {description} | {evidence_text} |")
        lines.append("")

    # Growth indicators table
    if growth:
        lines.append("### 🌱 올해 성장한 점")
        lines.append("")
        lines.append("| 성장 영역 | 근거 |")
        lines.append("|-----------|------|")
        for indicator in growth:
            aspect = indicator.get("aspect", "기타")
            description = indicator.get("description", "")
            progress_summary = indicator.get("progress_summary", "")
            before = indicator.get("before_examples", [])
            after = indicator.get("after_examples", [])

            evidence_parts = []
            if progress_summary:
                evidence_parts.append(f"**진전 사항:** {progress_summary}")
            if before:
                evidence_parts.append(f"**초기:** {', '.join(before[:2])}")
            if after:
                evidence_parts.append(f"**현재:** {', '.join(after[:2])}")

            evidence_text = "<br>".join(evidence_parts) if evidence_parts else "근거 없음"
            lines.append(f"| **{aspect}**: {description} | {evidence_text} |")
        lines.append("")

    return "\n".join(lines)


def _extract_section_content(content: str, section_header: str, next_section_prefix: str = "##") -> str:
    """Extract content of a specific section from markdown.

    Args:
        content: Full markdown content
        section_header: Header to look for (e.g., "## 🏆 Awards Cabinet")
        next_section_prefix: Prefix for next section (default "##")

    Returns:
        Extracted section content or empty string if not found
    """
    import re

    # Escape special regex characters in header
    escaped_header = re.escape(section_header)

    # Find section start
    pattern = rf'^{escaped_header}\s*$'
    match = re.search(pattern, content, re.MULTILINE)
    if not match:
        return ""

    start_pos = match.end()

    # Find next section of same or higher level
    next_section_pattern = rf'^{re.escape(next_section_prefix)} '
    next_match = re.search(next_section_pattern, content[start_pos:], re.MULTILINE)

    if next_match:
        end_pos = start_pos + next_match.start()
        return content[start_pos:end_pos].strip()

    return content[start_pos:].strip()


def _create_executive_summary(brief_content: str, feedback_content: str, output_dir: Path) -> str:
    """Create executive summary from brief and feedback reports.

    Args:
        brief_content: Brief report content
        feedback_content: Feedback report content
        output_dir: Output directory to find personal_development.json

    Returns:
        Executive summary markdown section
    """
    lines = ["## 🎯 한눈에 보기 (Executive Summary)", ""]
    lines.append("> 핵심 성과와 개선 포인트를 빠르게 파악하세요")
    lines.append("")

    # Extract key achievements from brief (awards section)
    awards_section = _extract_section_content(brief_content, "## 🏆 Awards Cabinet")
    if awards_section:
        # Count total awards
        import re
        award_matches = re.findall(r'\|\s*[^|]+\s*\|\s*([^|]+)\s*\|', awards_section)
        total_awards = len([m for m in award_matches if m.strip() and m.strip() not in ['어워드', '-----']])
        if total_awards > 0:
            lines.append(f"**🏆 획득 어워드**: {total_awards}개")

    # Extract highlights from brief
    highlights_section = _extract_section_content(brief_content, "## ✨ Growth Highlights")
    if highlights_section:
        import re
        highlight_matches = re.findall(r'\|\s*\d+\s*\|\s*([^|]+)\s*\|', highlights_section)
        if highlight_matches and len(highlight_matches) > 0:
            lines.append("")
            lines.append("**✨ 주요 성과 Top 3:**")
            for i, highlight in enumerate(highlight_matches[:3], 1):
                lines.append(f"{i}. {highlight.strip()}")

    # Extract improvement areas from personal development
    personal_dev_path = output_dir / "reviews" / "_temp_personal_dev.json"
    # Try to find personal_development.json in reviews subdirectories
    reviews_dir = output_dir / "reviews"
    if reviews_dir.exists():
        for repo_dir in reviews_dir.iterdir():
            if repo_dir.is_dir():
                pd_path = repo_dir / "personal_development.json"
                if pd_path.exists():
                    personal_dev_path = pd_path
                    break

    if personal_dev_path.exists():
        try:
            import json
            with open(personal_dev_path, "r", encoding="utf-8") as f:
                pd_data = json.load(f)

            improvements = pd_data.get("improvement_areas", [])[:2]
            if improvements:
                lines.append("")
                lines.append("**💡 주요 개선점 Top 2:**")
                for i, imp in enumerate(improvements, 1):
                    category = imp.get("category", "")
                    desc = imp.get("description", "")
                    lines.append(f"{i}. **{category}**: {desc}")

            # Extract next focus areas
            next_focus = pd_data.get("next_focus_areas", [])[:3]
            if next_focus:
                lines.append("")
                lines.append("**🎯 다음 집중 영역:**")
                for i, focus in enumerate(next_focus, 1):
                    lines.append(f"{i}. {focus}")
        except (json.JSONDecodeError, OSError):
            pass

    lines.append("")
    lines.append("---")
    lines.append("")
    return "\n".join(lines)


def _create_improved_toc() -> str:
    """Create improved table of contents with better structure."""
    lines = ["## 📑 목차", ""]

    sections = [
        ("1", "🎯 한눈에 보기", "핵심 성과와 개선점 요약"),
        ("2", "🏆 주요 성과", "어워드와 성장 하이라이트"),
        ("3", "💡 개선 피드백", "장점, 보완점, 실행 계획"),
        ("4", "📊 상세 분석", "월별 트렌드, 기술 스택, 협업, 회고"),
        ("5", "📝 부록", "개별 PR 리뷰 및 상세 사례"),
    ]

    for num, title, desc in sections:
        lines.append(f"{num}. **{title}** - {desc}")

    lines.append("")
    lines.append("---")
    lines.append("")
    return "\n".join(lines)


def _generate_integrated_full_report(
    output_dir: Path,
    repo_name: str,
    brief_content: str,
    feedback_report_path: Path,
) -> Path:
    """Generate an improved integrated report with better UX.

    Args:
        output_dir: Output directory for the integrated report
        repo_name: Repository name in owner/repo format
        brief_content: Brief report markdown content (from memory)
        feedback_report_path: Path to the feedback integrated report markdown file

    Returns:
        Path to the generated integrated report

    Raises:
        RuntimeError: If file operations fail
    """
    # Read feedback report with comprehensive error handling
    try:
        with open(feedback_report_path, "r", encoding="utf-8") as f:
            feedback_content = f.read()
    except FileNotFoundError:
        console.print(f"[warning]Feedback report not found at {feedback_report_path}[/]")
        feedback_content = "_Feedback report not available._"
    except PermissionError as exc:
        console.print(f"[warning]Permission denied reading {feedback_report_path}[/]")
        raise RuntimeError(f"Permission denied reading feedback report: {exc}") from exc
    except OSError as exc:
        console.print(f"[warning]Error reading feedback report: {exc}[/]")
        raise RuntimeError(f"Failed to read feedback report: {exc}") from exc

    # Extract key sections from brief
    awards_section = _extract_section_content(brief_content, "## 🏆 Awards Cabinet")
    highlights_section = _extract_section_content(brief_content, "## ✨ Growth Highlights")
    monthly_trends_section = _extract_section_content(brief_content, "## 📈 Monthly Trends")
    feedback_section = _extract_section_content(brief_content, "## 💡 Detailed Feedback")
    retrospective_section = _extract_section_content(brief_content, "## 🔍 Deep Retrospective Analysis")
    tech_stack_section = _extract_section_content(brief_content, "## 💻 Tech Stack Analysis")
    collaboration_section = _extract_section_content(brief_content, "## 🤝 PR 활동 요약")
    witch_section = _extract_section_content(brief_content, "## 🔮 마녀의 독설")

    # Extract key sections from feedback
    personal_dev_section = _extract_section_content(feedback_content, "## 👤 개인 성장 분석")
    strengths_section = _extract_section_content(feedback_content, "## ✨ 장점")
    improvements_section = _extract_section_content(feedback_content, "## 💡 보완점")
    growth_section = _extract_section_content(feedback_content, "## 🌱 올해 성장한 점")

    # Create executive summary
    exec_summary = _create_executive_summary(brief_content, feedback_content, output_dir)

    # Create improved TOC
    toc = _create_improved_toc()

    # Generate integrated report with improved structure
    integrated_content = f"""# 📊 {repo_name} 통합 분석 보고서

> 레포지토리 전체 분석과 PR 리뷰를 통합한 종합 보고서입니다.

{exec_summary}

{toc}

## 2. 🏆 주요 성과

> 이번 기간 동안 달성한 어워드와 성장 하이라이트

### 🏅 획득 어워드

{awards_section if awards_section else "_어워드 정보가 없습니다._"}

### ✨ 성장 하이라이트

{highlights_section if highlights_section else "_하이라이트 정보가 없습니다._"}

---

## 3. 💡 개선 피드백

> 구체적인 장점, 보완점, 실행 가능한 제안

{personal_dev_section if personal_dev_section else "_개인 성장 분석 정보가 없습니다._"}

### 🔮 마녀의 독설

{witch_section if witch_section else "_마녀의 독설 인사이트가 없습니다._"}

### 코드 품질 피드백

{feedback_section if feedback_section else "_상세 피드백 정보가 없습니다._"}

---

## 4. 📊 상세 분석

> 데이터 기반의 심층 분석 (필요한 섹션을 클릭하여 펼쳐보세요)

<details>
<summary><b>📈 월별 활동 트렌드</b> (클릭하여 펼치기)</summary>

{monthly_trends_section if monthly_trends_section else "_월별 트렌드 정보가 없습니다._"}

</details>

<details>
<summary><b>💻 기술 스택 분석</b> (클릭하여 펼치기)</summary>

{tech_stack_section if tech_stack_section else "_기술 스택 정보가 없습니다._"}

</details>

<details>
<summary><b>🤝 협업 분석</b> (클릭하여 펼치기)</summary>

{collaboration_section if collaboration_section else "_협업 정보가 없습니다._"}

</details>

<details>
<summary><b>🔍 심층 회고</b> (클릭하여 펼치기)</summary>

{retrospective_section if retrospective_section else "_회고 분석 정보가 없습니다._"}

</details>

---

## 5. 📝 부록

> 개별 PR 리뷰 및 상세 사례 (필요시 펼쳐보세요)

<details>
<summary><b>📝 상세 사례</b> (클릭하여 펼치기)</summary>

{growth_section if growth_section else ""}

{strengths_section if strengths_section else ""}

{improvements_section if improvements_section else ""}

</details>

---

<div align="center">

*Generated by GitHub Feedback Analysis Tool*
*Report generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*

</div>
"""

    # Save integrated report with comprehensive error handling
    from .utils import FileSystemManager

    try:
        FileSystemManager.ensure_directory(output_dir)
    except PermissionError as exc:
        raise RuntimeError(
            f"Permission denied creating directory {output_dir}: {exc}"
        ) from exc
    except OSError as exc:
        raise RuntimeError(
            f"Failed to create directory {output_dir}: {exc}"
        ) from exc

    integrated_report_path = output_dir / "integrated_full_report.md"

    # Validate path before writing
    if integrated_report_path.exists() and not integrated_report_path.is_file():
        raise RuntimeError(
            f"Cannot write to {integrated_report_path}: path exists but is not a file"
        )

    try:
        with open(integrated_report_path, "w", encoding="utf-8") as f:
            f.write(integrated_content)
    except PermissionError as exc:
        raise RuntimeError(
            f"Permission denied writing to {integrated_report_path}: {exc}"
        ) from exc
    except OSError as exc:
        # Check for specific errors
        if exc.errno == 28:  # ENOSPC - No space left on device
            raise RuntimeError(
                f"No space left on device while writing to {integrated_report_path}"
            ) from exc
        raise RuntimeError(
            f"Failed to write integrated report to {integrated_report_path}: {exc}"
        ) from exc

    return integrated_report_path


def _generate_reports_and_artifacts(
    metrics: MetricSnapshot,
    reporter: Reporter,
    output_dir_resolved: Path,
) -> tuple[List[tuple[str, Path]], Optional[str]]:
    """Generate report artifacts.

    Args:
        metrics: Metrics snapshot
        reporter: Reporter instance
        output_dir_resolved: Output directory path

    Returns:
        Tuple of (artifacts, brief_content)
    """
    console.print()
    console.rule("Phase 4: Report Generation")
    metrics_payload = cli_metrics.prepare_metrics_payload(metrics)
    artifacts, brief_content = _generate_artifacts(
        metrics, reporter, output_dir_resolved, metrics_payload, save_intermediate_report=True
    )
    return artifacts, brief_content


def _run_pr_reviews(
    config: Config,
    repo_input: str,
    output_dir_resolved: Path,
) -> tuple[Path | None, list[tuple[int, Path, Path, Path]]]:
    """Run PR review analysis.

    Args:
        config: Configuration object
        repo_input: Repository name
        output_dir_resolved: Output directory

    Returns:
        Tuple of (feedback_report_path, pr_results)
    """
    console.print()
    console.rule("Phase 6: PR Review Analysis")
    console.print("[accent]Analyzing all your PRs with AI-powered reviews...[/]")
    feedback_report_path, pr_results = _run_feedback_analysis(
        config=config,
        repo_input=repo_input,
        output_dir=output_dir_resolved,
    )

    if feedback_report_path:
        console.print(f"[success]✓ PR review analysis complete[/]")
    else:
        console.print("[warning]⚠ PR review analysis skipped or failed[/]")

    return feedback_report_path, pr_results


def _generate_final_report(
    output_dir_resolved: Path,
    repo_input: str,
    brief_content: Optional[str],
    feedback_report_path: Optional[Path],
) -> Optional[Path]:
    """Generate integrated full report.

    Args:
        output_dir_resolved: Output directory
        repo_input: Repository name
        brief_content: Brief report content
        feedback_report_path: Path to feedback report

    Returns:
        Path to integrated report or None if not generated
    """
    console.print()
    console.rule("Phase 7: Final Report Generation")

    integrated_report_path = None
    if feedback_report_path and brief_content:
        console.print("[accent]Creating integrated full report...[/]")
        try:
            integrated_report_path = _generate_integrated_full_report(
                output_dir=output_dir_resolved,
                repo_name=repo_input,
                brief_content=brief_content,
                feedback_report_path=feedback_report_path,
            )
            console.print(f"[success]✓ Integrated full report generated[/]")
        except Exception as exc:
            console.print(f"[warning]Failed to generate integrated report: {exc}[/]")
    elif not feedback_report_path:
        console.print("[warning]Feedback report not available, skipping integrated report generation[/]")
    else:
        console.print("[warning]Brief report content not available, skipping integrated report generation[/]")

    return integrated_report_path


def _run_year_in_review_analysis(
    config: Config,
    output_dir: Path,
    year: Optional[int] = None,
) -> None:
    """Run year-in-review analysis across all active repositories.

    Args:
        config: Configuration object
        output_dir: Output directory for reports
        year: Specific year to analyze (default: current year)
    """
    from datetime import datetime
    from .year_in_review_reporter import YearInReviewReporter, RepositoryAnalysis

    if year is None:
        year = datetime.now().year

    console.print()
    console.print(f"[accent]🎊 Starting Year-in-Review Analysis for {year}[/]")
    console.rule(f"Year {year} in Review")

    # Initialize collector
    try:
        collector = Collector(config)
    except ValueError as exc:
        console.print_error(exc)
        raise typer.Exit(code=1) from exc

    # Get authenticated user
    author = cli_repository.get_authenticated_user(collector)

    # Discover repositories
    console.print()
    console.rule("Phase 1: Repository Discovery")
    with console.status(
        f"[accent]Finding repositories you contributed to in {year}...", spinner="dots"
    ):
        repositories = collector.get_year_in_review_repositories(year=year, min_contributions=3)

    if not repositories:
        console.print(f"[warning]No repositories found with contributions in {year}.[/]")
        console.print("[info]Suggestions:[/]")
        console.print("  • Try a different year with [accent]--year[/]")
        console.print("  • Check if your PAT has access to your repositories")
        raise typer.Exit(code=1)

    console.print(f"[success]✓ Found {len(repositories)} repositories with your contributions[/]")
    console.print()

    # Display repositories
    console.print("[info]Repositories to analyze:[/]")
    for idx, repo in enumerate(repositories, 1):
        full_name = repo.get("full_name", "")
        year_commits = repo.get("_year_commits", 0)
        console.print(f"  {idx}. {full_name} ({year_commits} commits)")
    console.print()

    # Analyze each repository in parallel
    console.print()
    console.rule("Phase 2: Repository Analysis")
    console.print(f"[accent]Analyzing {len(repositories)} repositories in parallel...[/]")

    output_dir_resolved = cli_helpers.resolve_output_dir(output_dir)

    # Create analysis tasks
    analysis_tasks = {}
    for repo_data in repositories:
        full_name = repo_data.get("full_name", "")
        if not full_name:
            continue

        key = f"repo_{full_name.replace('/', '__')}"
        analysis_tasks[key] = (
            _analyze_single_repository_for_year_review,
            (config, full_name, year, output_dir_resolved),
            f"Repository: {full_name}",
        )

    # Run analyses in parallel
    analysis_results = cli_helpers.run_parallel_tasks(
        analysis_tasks,
        max_workers=3,  # Limit concurrency to avoid rate limits
        timeout=600,  # 10 minutes per repository
        task_type=TaskType.ANALYSIS,
    )

    # Collect successful analyses
    repository_analyses = []
    for repo_data in repositories:
        full_name = repo_data.get("full_name", "")
        key = f"repo_{full_name.replace('/', '__')}"

        if key in analysis_results and analysis_results[key] is not None:
            repo_analysis = analysis_results[key]
            if repo_analysis:
                repository_analyses.append(repo_analysis)
        else:
            console.print(f"[warning]⚠ Skipped {full_name} due to analysis failure[/]")

    if not repository_analyses:
        console.print("[danger]All repository analyses failed.[/]")
        raise typer.Exit(code=1)

    console.print(f"[success]✓ Successfully analyzed {len(repository_analyses)} repositories[/]")

    # Generate year-in-review report
    console.print()
    console.rule("Phase 3: Generating Year-in-Review Report")

    year_reporter = YearInReviewReporter(output_dir=output_dir_resolved / "year-in-review")
    report_path = year_reporter.create_year_in_review_report(
        year=year,
        username=author,
        repository_analyses=repository_analyses,
    )

    # Display summary
    console.print()
    console.rule("Summary")
    console.print(f"[success]✓ Year-in-review analysis complete for {year}[/]")
    console.print(f"[success]✓ Analyzed {len(repository_analyses)} repositories[/]")
    console.print()
    console.print("[info]📊 Final Report:[/]")
    console.print(f"  • [accent]{report_path}[/]")
    console.print()
    console.print("[info]💡 Next steps:[/]")
    console.print(f"  • View the report: [accent]cat {report_path}[/]")
    console.print("  • Review individual repository reports in: [accent]reports/reviews/[/]")


def _get_year_in_review_metrics_dir(output_dir: Path) -> Path:
    """Return the directory that stores per-repository metrics for Year-in-Review."""

    return output_dir / "year-in-review" / "metrics"


def _get_year_in_review_metrics_path(output_dir: Path, repo_name: str) -> Path:
    """Return the canonical metrics path for the given repository."""

    safe_repo = repo_name.replace("/", "__")
    return _get_year_in_review_metrics_dir(output_dir) / f"{safe_repo}.json"


def _get_legacy_year_in_review_metrics_path(output_dir: Path, repo_name: str) -> Path:
    """Return the legacy metrics path that stored metrics inside repo-named folders."""

    safe_repo = repo_name.replace("/", "__")
    return output_dir / safe_repo / "metrics.json"


def _load_year_in_review_metrics_data(
    primary_path: Path, legacy_path: Path
) -> tuple[dict, bool]:
    """Load metrics data from the new or legacy path.

    Returns:
        Tuple containing the loaded metrics (or empty dict) and a flag indicating whether
        the data originated from the legacy path.
    """

    import json

    for path, is_legacy in ((primary_path, False), (legacy_path, True)):
        if path.exists():
            try:
                with path.open("r", encoding="utf-8") as handle:
                    return json.load(handle), is_legacy
            except Exception:
                return {}, is_legacy

    return {}, False


def _cleanup_legacy_metrics_path(legacy_path: Path) -> None:
    """Remove the legacy metrics file/directory if it exists and is now unused."""

    try:
        if legacy_path.exists():
            legacy_path.unlink()
        parent = legacy_path.parent
        if parent.exists():
            parent.rmdir()
    except OSError:
        # If the directory isn't empty or can't be removed, ignore silently.
        pass


def _analyze_single_repository_for_year_review(
    config: Config,
    repo_name: str,
    year: int,
    output_dir: Path,
) -> Optional[RepositoryAnalysis]:
    """Analyze a single repository for year-in-review.

    Args:
        config: Configuration object
        repo_name: Repository name (owner/repo)
        year: Year being analyzed
        output_dir: Output directory

    Returns:
        RepositoryAnalysis object or None if analysis fails
    """
    import json
    from datetime import datetime, timedelta
    from .year_in_review_reporter import RepositoryAnalysis

    try:
        # Get authenticated user
        collector = Collector(config)
        author = collector.get_authenticated_user()
        safe_repo = repo_name.replace("/", "__")

        # Calculate year date range
        since = datetime(year, 1, 1)
        until = datetime(year, 12, 31, 23, 59, 59)

        # Get PR count for the year
        filters = AnalysisFilters(
            include_branches=[],
            exclude_branches=[],
            include_paths=[],
            exclude_paths=[],
            include_languages=[],
            exclude_bots=True,
        )

        # Collect PRs authored in the year
        pr_numbers = collector.list_authored_pull_requests(
            repo=repo_name,
            author=author,
            state="all",
        )

        # Run feedback analysis (generates integrated_report.md and personal_development.json)
        feedback_report_path, pr_results = _run_feedback_analysis(
            config=config,
            repo_input=repo_name,
            output_dir=output_dir,
        )

        # Collect detailed feedback for communication skills analysis
        console.print(f"[dim]📊 Collecting detailed feedback for {repo_name}...[/]")
        analyzer = Analyzer(web_base_url=config.server.web_url)
        detailed_feedback_snapshot = cli_data_collection.collect_detailed_feedback(
            collector=collector,
            analyzer=analyzer,
            config=config,
            repo=repo_name,
            since=since,
            filters=filters,
            author=author,
        )

        # Save detailed feedback to metrics.json for later retrieval
        if detailed_feedback_snapshot:
            console.print(f"[dim]💾 Saving detailed feedback to metrics.json...[/]")
            metrics_path = _get_year_in_review_metrics_path(output_dir, repo_name)
            legacy_metrics_path = _get_legacy_year_in_review_metrics_path(output_dir, repo_name)
            from .utils import FileSystemManager

            metrics_dir = metrics_path.parent
            FileSystemManager.ensure_directory(metrics_dir)

            metrics_data, loaded_from_legacy = _load_year_in_review_metrics_data(
                metrics_path, legacy_metrics_path
            )

            # Add detailed_feedback to metrics
            metrics_data["detailed_feedback"] = detailed_feedback_snapshot.to_dict()

            # Save updated metrics
            import json

            with metrics_path.open("w", encoding="utf-8") as f:
                json.dump(metrics_data, f, indent=2, ensure_ascii=False)

            if loaded_from_legacy:
                _cleanup_legacy_metrics_path(legacy_metrics_path)

            console.print(f"[success]✅ Saved detailed feedback to {metrics_path}[/]")

        # Load personal development data
        reviews_dir = output_dir / "reviews" / safe_repo
        personal_dev_path = reviews_dir / "personal_development.json"

        strengths = []
        improvements = []
        growth_indicators = []
        tech_stack = {}

        # Communication skills data
        commit_message_quality = None
        pr_title_quality = None
        review_tone_quality = None
        issue_quality = None
        commit_stats = {}
        pr_title_stats = {}
        review_tone_stats = {}
        issue_stats = {}

        if personal_dev_path.exists():
            with open(personal_dev_path, "r", encoding="utf-8") as f:
                personal_dev = json.load(f)

            strengths = personal_dev.get("strengths", [])
            improvements = personal_dev.get("improvement_areas", [])
            growth_indicators = personal_dev.get("growth_indicators", [])

        # Load metrics.json for detailed feedback (commit message quality, review tone, etc.)
        metrics_path = _get_year_in_review_metrics_path(output_dir, repo_name)
        legacy_metrics_path = _get_legacy_year_in_review_metrics_path(output_dir, repo_name)
        metrics_data, _ = _load_year_in_review_metrics_data(metrics_path, legacy_metrics_path)
        if metrics_data:
            try:
                # Extract detailed feedback
                detailed_feedback = metrics_data.get("detailed_feedback", {})

                # Commit message quality
                if "commit_feedback" in detailed_feedback:
                    cf = detailed_feedback["commit_feedback"]
                    total_commits = cf.get("total_commits", 0)
                    good_messages = cf.get("good_messages", 0)
                    poor_messages = cf.get("poor_messages", 0)

                    if total_commits > 0:
                        commit_message_quality = (good_messages / total_commits) * 100
                        commit_stats = {
                            "total": total_commits,
                            "good": good_messages,
                            "poor": poor_messages
                        }

                # PR title quality
                if "pr_title_feedback" in detailed_feedback:
                    pf = detailed_feedback["pr_title_feedback"]
                    total_prs = pf.get("total_prs", 0)
                    clear_titles = pf.get("clear_titles", 0)
                    unclear_titles = pf.get("unclear_titles", 0)

                    if total_prs > 0:
                        pr_title_quality = (clear_titles / total_prs) * 100
                        pr_title_stats = {
                            "total": total_prs,
                            "clear": clear_titles,
                            "unclear": unclear_titles
                        }

                # Review tone quality
                if "review_tone_feedback" in detailed_feedback:
                    rtf = detailed_feedback["review_tone_feedback"]
                    constructive = rtf.get("constructive_reviews", 0)
                    harsh = rtf.get("harsh_reviews", 0)
                    neutral = rtf.get("neutral_reviews", 0)
                    total_reviews = constructive + harsh + neutral

                    if total_reviews > 0:
                        review_tone_quality = (constructive / total_reviews) * 100
                        review_tone_stats = {
                            "constructive": constructive,
                            "harsh": harsh,
                            "neutral": neutral
                        }

                # Issue quality
                if "issue_feedback" in detailed_feedback:
                    isf = detailed_feedback["issue_feedback"]
                    total_issues = isf.get("total_issues", 0)
                    clear_issues = isf.get("well_described", 0)
                    unclear_issues = isf.get("poorly_described", 0)

                    if total_issues > 0:
                        issue_quality = (clear_issues / total_issues) * 100
                        issue_stats = {
                            "total": total_issues,
                            "clear": clear_issues,
                            "unclear": unclear_issues
                        }

                console.print(f"[success]✅ Loaded communication skills data from metrics.json[/]")
            except Exception as e:
                console.print(f"[warning]⚠️  Could not load metrics.json: {e}[/]")

        # Collect tech stack data
        try:
            # Get PR metadata for tech stack analysis
            # Use a much broader time window to get sufficient data for tech stack analysis
            # Instead of only PRs created in the target year, analyze recent repository activity
            from datetime import timedelta
            tech_stack_since = datetime(year - 2, 1, 1)  # Look back 2 years for better tech stack data

            console.print(f"[dim]🔍 Fetching PRs for tech stack analysis (since {tech_stack_since.year}-01-01)...[/]")
            _, pr_metadata = collector.list_pull_requests(
                repo=repo_name,
                since=tech_stack_since,  # Use broader window for tech stack analysis
                filters=filters,
                author=None  # Analyze all PRs in repo, not just user's
            )

            console.print(f"[dim]📊 Analyzing tech stack from {len(pr_metadata)} PRs (since {tech_stack_since.year})[/]")

            if not pr_metadata:
                console.print(f"[warning]⚠️  No PRs found for tech stack analysis in {repo_name}[/]")
            else:
                tech_stack_snapshot = collector.collect_tech_stack(
                    repo=repo_name,
                    pr_metadata=pr_metadata
                )

                if tech_stack_snapshot:
                    tech_stack = {lang: count for lang, count in tech_stack_snapshot.items()}
                    console.print(f"[success]✅ Found {len(tech_stack)} technologies in tech stack[/]")
                    # Debug: Print top 5 technologies
                    if tech_stack:
                        sorted_tech = sorted(tech_stack.items(), key=lambda x: x[1], reverse=True)[:5]
                        tech_preview = ", ".join([f"{lang}({count})" for lang, count in sorted_tech])
                        console.print(f"[dim]   Top technologies: {tech_preview}[/]")
                else:
                    console.print(f"[warning]⚠️  Tech stack analysis returned empty for {repo_name}[/]")
        except Exception as exc:
            import traceback
            console.print(f"[error]❌ Could not collect tech stack for {repo_name}:[/]")
            console.print(f"[error]   Error: {exc}[/]")
            console.print(f"[dim]{traceback.format_exc()}[/]")

        # Get total commit count
        owner, repo = repo_name.split("/", 1)
        all_commits = collector.api_client.get_user_commits_in_repo(
            owner, repo, author, max_pages=10
        )
        total_commits = len(all_commits)

        # Get commits in the year
        year_commits_params = {
            "author": author,
            "since": since.isoformat() + "Z",
            "until": until.isoformat() + "Z",
        }
        year_commits = collector.api_client.request_all(
            f"/repos/{owner}/{repo}/commits",
            params=year_commits_params,
        )

        return RepositoryAnalysis(
            full_name=repo_name,
            pr_count=len(pr_results),
            commit_count=total_commits,
            year_commits=len(year_commits),
            integrated_report_path=feedback_report_path,
            personal_dev_path=personal_dev_path if personal_dev_path.exists() else None,
            strengths=strengths,
            improvements=improvements,
            growth_indicators=growth_indicators,
            tech_stack=tech_stack,
            commit_message_quality=commit_message_quality,
            pr_title_quality=pr_title_quality,
            review_tone_quality=review_tone_quality,
            issue_quality=issue_quality,
            commit_stats=commit_stats,
            pr_title_stats=pr_title_stats,
            review_tone_stats=review_tone_stats,
            issue_stats=issue_stats,
        )

    except Exception as exc:
        console.print(f"[warning]Failed to analyze {repo_name}: {exc}[/]")
        return None


def _display_final_summary(
    author: str,
    repo_input: str,
    pr_results: list,
    integrated_report_path: Optional[Path],
    artifacts: List[tuple[str, Path]],
) -> None:
    """Display final summary of the analysis.

    Args:
        author: GitHub username
        repo_input: Repository name
        pr_results: PR review results
        integrated_report_path: Path to integrated report
        artifacts: List of generated artifacts
    """
    console.print()
    console.rule("Summary")
    console.print(f"[success]✓ Complete analysis for {author}[/]")
    console.print(f"[success]✓ Repository:[/] {repo_input}")
    console.print(f"[success]✓ PRs reviewed:[/] {len(pr_results)}")
    console.print()

    if integrated_report_path:
        console.print("[info]📊 Final Report:[/]")
        console.print(f"  • [accent]{integrated_report_path}[/]")
        console.print()
        console.print("[info]💡 Next steps:[/]")
        console.print(f"  • View the full report: [accent]cat {integrated_report_path}[/]")
        console.print("  • View individual PR reviews in: [accent]reports/reviews/[/]")
    else:
        console.print("[warning]No integrated report was generated.[/]")
        console.print("[info]Individual artifacts:[/]")
        for label, path in artifacts:
            if "Internal report" not in label:
                console.print(f"  • {label}: [accent]{path}[/]")


@app.command()
def feedback(
    repo: Optional[str] = typer.Option(
        None,
        "--repo",
        "-r",
        help="Repository in owner/name format (e.g. microsoft/vscode)",
    ),
    output_dir: Path = typer.Option(
        Path("reports"),
        "--output",
        "-o",
        help="Output directory for reports",
    ),
    interactive: bool = typer.Option(
        False,
        "--interactive",
        "-i",
        help="Interactively select repository from suggestions",
    ),
    year_in_review: bool = typer.Option(
        False,
        "--year-in-review",
        "-y",
        help="Analyze all repositories you contributed to this year and generate a comprehensive annual report",
    ),
    year: Optional[int] = typer.Option(
        None,
        "--year",
        help="Specific year for year-in-review (default: current year)",
    ),
) -> None:
    """Analyze repository activity and generate detailed reports with PR feedback.

    This command collects commits, PRs, reviews, and issues from a GitHub
    repository, analyzes all PRs authored by you, then generates comprehensive
    reports with insights and recommendations.

    With --year-in-review, analyzes all repositories you contributed to during
    the specified year and generates a comprehensive annual summary report.

    Examples:
        gfa feedback --repo torvalds/linux
        gfa feedback --repo myorg/myrepo --output custom_reports/
        gfa feedback --interactive
        gfa feedback --year-in-review
        gfa feedback --year-in-review --year 2024
    """
    from datetime import datetime, timedelta, timezone

    # Initialize configuration and components
    config = cli_helpers.load_config()

    # Handle year-in-review mode
    if year_in_review:
        _run_year_in_review_analysis(config, output_dir, year)
        return

    months = config.defaults.months
    filters = AnalysisFilters(
        include_branches=[],
        exclude_branches=[],
        include_paths=[],
        exclude_paths=[],
        include_languages=[],
        exclude_bots=True,
    )

    try:
        collector = Collector(config)
    except ValueError as exc:
        console.print_error(exc)
        console.print("[info]Hint:[/] Check your GitHub token with [accent]gfa show-config[/]")
        raise typer.Exit(code=1) from exc

    # Select repository
    if interactive or repo is None:
        repo_input = cli_repository.select_repository_interactive(collector)
        if not repo_input:
            console.print("[warning]No repository selected.[/]")
            raise typer.Exit(code=0)
    else:
        repo_input = repo.strip()

    # Validate repository format
    try:
        validate_repo_format(repo_input)
    except ValueError as exc:
        console.print_validation_error(str(exc))
        console.print("[info]Example:[/] [accent]gfa feedback --repo torvalds/linux[/]")
        raise typer.Exit(code=1) from exc

    # Initialize analyzer and reporter
    analyzer = Analyzer(web_base_url=config.server.web_url)
    output_dir_resolved = cli_helpers.resolve_output_dir(output_dir)

    # Create LLM client for reporter (used for generating summary quotes)
    from .llm import LLMClient
    llm_client = LLMClient(
        endpoint=config.llm.endpoint,
        model=config.llm.model,
        timeout=config.llm.timeout,
        web_url=config.server.web_url,
    )
    reporter = Reporter(output_dir=output_dir_resolved, llm_client=llm_client, web_url=config.server.web_url)

    # Execute analysis workflow
    author = cli_repository.get_authenticated_user(collector)
    collection = cli_data_collection.collect_personal_activity(collector, repo_input, months, filters, author)

    # Collect detailed feedback
    console.print()
    console.rule("Phase 2: Detailed Feedback Analysis")
    from github_feedback.constants import DAYS_PER_MONTH_APPROX
    since = datetime.now(timezone.utc) - timedelta(days=DAYS_PER_MONTH_APPROX * max(months, 1))
    detailed_feedback_snapshot = cli_data_collection.collect_detailed_feedback(
        collector, analyzer, config, repo_input, since, filters, author
    )

    # Collect year-end data
    console.print()
    console.rule("Phase 2.5: Year-End Review Data")
    monthly_trends_data, tech_stack_data, collaboration_data = cli_data_collection.collect_yearend_data(
        collector, repo_input, since, filters, author
    )

    # Compute metrics and display
    metrics = cli_metrics.compute_and_display_metrics(
        analyzer, collection, detailed_feedback_snapshot,
        monthly_trends_data, tech_stack_data, collaboration_data
    )

    # Generate reports
    artifacts, brief_content = _generate_reports_and_artifacts(metrics, reporter, output_dir_resolved)

    # Run PR reviews
    feedback_report_path, pr_results = _run_pr_reviews(config, repo_input, output_dir_resolved)

    # Generate final integrated report
    integrated_report_path = _generate_final_report(
        output_dir_resolved, repo_input, brief_content, feedback_report_path
    )

    # Display summary
    _display_final_summary(author, repo_input, pr_results, integrated_report_path, artifacts)


@app.callback()
def main_callback(
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose output for debugging",
    ),
    quiet: bool = typer.Option(
        False,
        "--quiet",
        "-q",
        help="Suppress non-essential output",
    ),
    no_color: bool = typer.Option(
        False,
        "--no-color",
        help="Disable colored output",
    ),
) -> None:
    """CLI entry-point callback for shared initialisation."""
    from .christmas_theme import is_christmas_season, get_christmas_banner

    # Set console modes
    console.set_verbose(verbose)
    console.set_quiet(quiet)

    if no_color:
        os.environ["NO_COLOR"] = "1"

    # Display Christmas decorations if in season (Nov 1 - Dec 31) and not in quiet mode
    disable_theme = os.getenv("GHF_NO_THEME", "").lower() in ("1", "true", "yes")
    if is_christmas_season() and not disable_theme and not quiet:
        console.print(get_christmas_banner())




@config_app.command("show")
def show_config() -> None:
    """Display current configuration settings.

    Shows your GitHub server URLs, LLM endpoint, and default settings.
    Sensitive values like tokens are masked for security.
    """

    _print_config_summary()


def _print_config_summary() -> None:
    """Render the current configuration in either table or plain format."""

    config = cli_helpers.load_config()
    data = config.to_display_dict()

    if Table is None:
        console.print("GitHub Feedback Configuration")
        for section, values in data.items():
            console.print(f"[{section}]")
            for key, value in values.items():
                console.print(f"{key} = {value}")
            console.print("")
        return

    table = Table(
        title="GitHub Feedback Configuration",
        box=box.ROUNDED,
        title_style="title",
        border_style="frame",
        expand=True,
        show_lines=True,
    )
    table.add_column("Section", style="label", no_wrap=True)
    table.add_column("Values", style="value")

    for section, values in data.items():
        rendered_values = "\n".join(f"[label]{k}[/]: [value]{v}[/]" for k, v in values.items())
        table.add_row(f"[accent]{section}[/]", rendered_values)

    console.print(table)


@config_app.command("set")
def config_set(
    key: str = typer.Argument(..., help="Configuration key in dot notation (e.g. llm.model)"),
    value: str = typer.Argument(..., help="Value to set"),
) -> None:
    """Set a configuration value.

    Examples:
        gfa config set llm.model gpt-4
        gfa config set llm.endpoint https://api.openai.com/v1/chat/completions
        gfa config set defaults.months 6
    """
    try:
        config = Config.load()
        config.set_value(key, value)
        config.dump()
        console.print(f"[success]✓ Configuration updated:[/] {key} = {value}")
    except ValueError as exc:
        console.print_error(exc)
        raise typer.Exit(code=1) from exc


@config_app.command("get")
def config_get(
    key: str = typer.Argument(..., help="Configuration key in dot notation (e.g. llm.model)"),
) -> None:
    """Get a configuration value.

    Examples:
        gfa config get llm.model
        gfa config get defaults.months
    """
    try:
        config = Config.load()
        value = config.get_value(key)
        console.print(f"{key} = {value}")
    except ValueError as exc:
        console.print_error(exc)
        raise typer.Exit(code=1) from exc


@config_app.command("hosts")
def config_hosts(
    action: str = typer.Argument(
        ...,
        help="Action to perform: list, add, or remove"
    ),
    host: Optional[str] = typer.Argument(
        None,
        help="Host URL (required for add/remove actions)"
    ),
) -> None:
    """Manage custom enterprise hosts.

    Examples:
        gfa config hosts list
        gfa config hosts add https://github.company.com
        gfa config hosts remove https://github.company.com
    """
    try:
        config = Config.load()

        if action == "list":
            if not config.server.custom_enterprise_hosts:
                console.print("[info]No custom enterprise hosts saved.[/]")
                console.print("[dim]Add hosts using:[/] gfa config hosts add <host-url>")
            else:
                console.print("[accent]Custom Enterprise Hosts:[/]\n")
                for idx, saved_host in enumerate(config.server.custom_enterprise_hosts, 1):
                    console.print(f"  {idx}. {saved_host}")

        elif action == "add":
            if not host:
                console.print("[danger]Error:[/] Host URL is required for 'add' action")
                console.print("[info]Usage:[/] gfa config hosts add <host-url>")
                raise typer.Exit(code=1)

            # Validate and normalize host
            host = host.strip()
            if not host.startswith(("http://", "https://")):
                host = f"https://{host}"

            try:
                validate_url(host, "Enterprise host")
            except ValueError as exc:
                console.print_validation_error(str(exc))
                raise typer.Exit(code=1) from exc

            host = host.rstrip("/")

            if host in config.server.custom_enterprise_hosts:
                console.print(f"[warning]Host '{host}' is already in your custom list[/]")
            else:
                config.server.custom_enterprise_hosts.append(host)
                config.dump()
                console.print(f"[success]✓ Added '{host}' to your custom host list[/]")

        elif action == "remove":
            if not host:
                console.print("[danger]Error:[/] Host URL is required for 'remove' action")
                console.print("[info]Usage:[/] gfa config hosts remove <host-url>")
                raise typer.Exit(code=1)

            # Normalize host for comparison
            host = host.strip().rstrip("/")
            if not host.startswith(("http://", "https://")):
                host = f"https://{host}"

            if host in config.server.custom_enterprise_hosts:
                config.server.custom_enterprise_hosts.remove(host)
                config.dump()
                console.print(f"[success]✓ Removed '{host}' from your custom host list[/]")
            else:
                console.print(f"[warning]Host '{host}' not found in your custom list[/]")
                console.print("[info]Use 'gfa config hosts list' to see saved hosts[/]")

        else:
            console.print_error(f"Unknown action '{action}'")
            console.print("[info]Valid actions:[/] list, add, remove")
            raise typer.Exit(code=1)

    except ValueError as exc:
        console.print_error(exc)
        raise typer.Exit(code=1) from exc


@app.command(name="list-repos")
def list_repos(
    sort: str = typer.Option(
        "updated",
        "--sort",
        "-s",
        help="Sort field (updated, created, pushed, full_name)",
    ),
    limit: int = typer.Option(
        20,
        "--limit",
        "-l",
        help="Maximum number of repositories to display",
    ),
    org: Optional[str] = typer.Option(
        None,
        "--org",
        "-o",
        help="Filter by organization name",
    ),
) -> None:
    """List repositories accessible to the authenticated user.

    This command fetches repositories from GitHub and displays them in a
    formatted table. You can filter by organization and sort by various
    criteria.

    Examples:
        gfa list-repos
        gfa list-repos --sort stars --limit 10
        gfa list-repos --org myorganization
    """
    config = cli_helpers.load_config()

    try:
        collector = Collector(config)
    except ValueError as exc:
        console.print_error(exc)
        raise typer.Exit(code=1) from exc

    with console.status("[accent]Fetching repositories...", spinner="bouncingBar"):
        if org:
            repos = collector.list_org_repositories(org, sort)
        else:
            repos = collector.list_user_repositories(sort)

    if not repos:
        console.print("[warning]No repositories found.[/]")
        if org:
            console.print(f"[info]Organization:[/] {org}")
        raise typer.Exit(code=0)

    # Limit the results
    repos = repos[:limit]

    # Display repositories using helper function
    create_repository_table(
        repos=repos,
        title=f"{'Organization' if org else 'Your'} Repositories",
        include_rank=False,
        include_activity=False,
        console=console,
    )


@app.command(name="suggest-repos")
def suggest_repos(
    limit: int = typer.Option(
        10,
        "--limit",
        "-l",
        help="Maximum number of suggestions",
    ),
    days: int = typer.Option(
        90,
        "--days",
        "-d",
        help="Filter repos updated within this many days",
    ),
    sort: str = typer.Option(
        "activity",
        "--sort",
        "-s",
        help="Sort criteria (updated, stars, activity)",
    ),
) -> None:
    """Suggest repositories for analysis based on activity and recency.

    This command recommends repositories that are actively maintained and
    likely to benefit from analysis. Suggestions are based on recent updates,
    stars, forks, and overall activity.

    Examples:
        gfa suggest-repos
        gfa suggest-repos --limit 5 --days 30
        gfa suggest-repos --sort stars
    """
    config = cli_helpers.load_config()

    try:
        collector = Collector(config)
    except ValueError as exc:
        console.print_error(exc)
        raise typer.Exit(code=1) from exc

    with console.status("[accent]Analyzing repositories...", spinner="bouncingBar"):
        suggestions = collector.suggest_repositories(
            limit=limit, min_activity_days=days, sort_by=sort
        )

    if not suggestions:
        console.print("[warning]No repository suggestions found.[/]")
        console.print(
            f"[info]Try increasing the activity window with [accent]--days[/] (current: {days})"
        )
        raise typer.Exit(code=0)

    # Display repository suggestions using helper function
    create_repository_table(
        repos=suggestions,
        title="Suggested Repositories for Analysis",
        include_rank=True,
        include_activity=True,
        console=console,
    )
    console.print_section_separator()
    console.print(
        "[info]To analyze a repository, use:[/] [accent]gfa feedback --repo <owner/name>[/]"
    )


@app.command(name="clear-cache")
def clear_cache() -> None:
    """Clear the API response cache.

    This can help resolve issues with stale or corrupted cached data
    that may cause JSON parsing errors or other unexpected behavior.

    Examples:
        gfa clear-cache
    """
    from .api_client import GitHubApiClient

    console.print("[info]Clearing API cache...[/]")
    GitHubApiClient.clear_cache()


# Keep show-config as a deprecated alias for backward compatibility
@app.command(name="show-config", hidden=True, deprecated=True)
def show_config_deprecated() -> None:
    """Display current configuration settings (deprecated: use 'gfa config show')."""
    console.print("[warning]Note:[/] 'gfa show-config' is deprecated. Use 'gfa config show' instead.")
    console.print()
    _print_config_summary()
