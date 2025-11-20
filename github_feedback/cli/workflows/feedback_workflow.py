"""Feedback workflow helper functions for GitHub analysis.

This module contains helper functions for collecting detailed feedback data,
running feedback analysis, generating reports, and managing the feedback workflow.
"""

from __future__ import annotations

import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any, List, Optional, Tuple

import requests
import typer

from ...analyzer import Analyzer
from ...collector import Collector
from ...config import Config
from ...console import Console
from ...constants import COLLECTION_LIMITS, PARALLEL_CONFIG, TaskType
from ...exceptions import (
    CollectionError,
    CollectionTimeoutError,
    LLMAnalysisError,
    LLMTimeoutError,
)
from ...llm import LLMClient
from ...models import (
    AnalysisFilters,
    CollectionResult,
    DetailedFeedbackSnapshot,
    MetricSnapshot,
)
from ...reporter import Reporter
from ...review_reporter import ReviewReporter
from ...reviewer import Reviewer
from ...utils import FileSystemManager
from ..ui.display import render_metrics
from ..utils.metrics_utils import persist_metrics, prepare_metrics_payload
from ..utils.parallel import run_parallel_tasks, validate_collected_data


console = Console()
logger = logging.getLogger(__name__)


def _collect_detailed_feedback(
    collector: Collector,
    analyzer: Analyzer,
    config: Config,
    repo: str,
    since: datetime,
    filters: AnalysisFilters,
    author: Optional[str] = None,
) -> Optional[DetailedFeedbackSnapshot]:
    """Collect and analyze detailed feedback data in parallel.

    This function collects four types of feedback data and analyzes them using LLM:
    1. Commit messages - for quality analysis
    2. PR titles - for clarity analysis
    3. Review comments - for tone analysis
    4. Issue details - for quality analysis

    Args:
        collector: Data collector instance
        analyzer: Metrics analyzer instance
        config: Configuration with LLM settings
        repo: Repository name in owner/repo format
        since: Start date for data collection
        filters: Analysis filters to apply
        author: Optional GitHub username to filter by author

    Returns:
        DetailedFeedbackSnapshot with LLM analysis results,
        or None if collection/analysis fails

    Raises:
        KeyboardInterrupt: User interrupted the operation
    """
    start_time = time.time()
    console.print("[accent]Collecting detailed feedback data...", style="accent")

    logger.info(
        "Starting detailed feedback collection",
        extra={
            "component": "feedback_collector",
            "repo": repo,
            "since": since.isoformat(),
            "author": author or "all"
        }
    )

    try:
        # Prepare data collection tasks
        collection_tasks = {
            "commits": (
                lambda: collector.collect_commit_messages(
                    repo, since, filters, COLLECTION_LIMITS['commit_messages'], author
                ),
                (),
                "commit messages"
            ),
            "pr_titles": (
                lambda: collector.collect_pr_titles(
                    repo, since, filters, COLLECTION_LIMITS['pr_titles'], author
                ),
                (),
                "PR titles"
            ),
            "review_comments": (
                lambda: collector.collect_review_comments_detailed(
                    repo, since, filters, COLLECTION_LIMITS['review_comments'], author
                ),
                (),
                "review comments"
            ),
            "issues": (
                lambda: collector.collect_issue_details(
                    repo, since, filters, COLLECTION_LIMITS['issues'], author
                ),
                (),
                "issues"
            ),
        }

        # Collect data in parallel
        collected_data = run_parallel_tasks(
            collection_tasks,
            PARALLEL_CONFIG['max_workers_data_collection'],
            PARALLEL_CONFIG['collection_timeout'],
            task_type=TaskType.COLLECTION
        )

        # Validate and extract collected data
        commits_data = validate_collected_data(collected_data.get("commits"), "commits")
        pr_titles_data = validate_collected_data(collected_data.get("pr_titles"), "PR titles")
        review_comments_data = validate_collected_data(collected_data.get("review_comments"), "review comments")
        issues_data = validate_collected_data(collected_data.get("issues"), "issues")

        # Analyze using LLM
        llm_client = LLMClient(
            endpoint=config.llm.endpoint,
            model=config.llm.model,
            timeout=config.llm.timeout,
            max_files_in_prompt=config.llm.max_files_in_prompt,
            max_files_with_patch_snippets=config.llm.max_files_with_patch_snippets,
            web_url=config.server.web_url,
        )

        # Parallelize LLM analysis calls
        console.print("[accent]Analyzing feedback in parallel...", style="accent")

        analysis_tasks = {
            "commit_messages": (lambda: llm_client.analyze_commit_messages(commits_data, repo), (), "commits"),
            "pr_titles": (lambda: llm_client.analyze_pr_titles(pr_titles_data), (), "PR titles"),
            "review_tone": (lambda: llm_client.analyze_review_tone(review_comments_data), (), "review tone"),
            "issue_quality": (lambda: llm_client.analyze_issue_quality(issues_data, config.server.web_url, repo), (), "issues"),
            "personal_development": (lambda: llm_client.analyze_personal_development(pr_titles_data, review_comments_data, repo), (), "personal development"),
        }

        results = run_parallel_tasks(
            analysis_tasks,
            PARALLEL_CONFIG['max_workers_llm_analysis'],
            PARALLEL_CONFIG['analysis_timeout'],
            task_type=TaskType.ANALYSIS
        )

        commit_analysis = results.get("commit_messages")
        pr_title_analysis = results.get("pr_titles")
        review_tone_analysis = results.get("review_tone")
        issue_analysis = results.get("issue_quality")
        personal_development_analysis = results.get("personal_development")

        # Build detailed feedback snapshot
        detailed_feedback_snapshot = analyzer.build_detailed_feedback(
            commit_analysis=commit_analysis,
            pr_title_analysis=pr_title_analysis,
            review_tone_analysis=review_tone_analysis,
            issue_analysis=issue_analysis,
            personal_development_analysis=personal_development_analysis,
        )

        elapsed_time = time.time() - start_time
        logger.info(
            "Detailed feedback analysis completed successfully",
            extra={
                "component": "feedback_collector",
                "repo": repo,
                "duration_seconds": round(elapsed_time, 2),
                "status": "success"
            }
        )
        console.print("[success]✓ Detailed feedback analysis complete", style="success")
        return detailed_feedback_snapshot

    except (requests.RequestException, json.JSONDecodeError, ValueError, KeyError) as exc:
        elapsed_time = time.time() - start_time
        logger.warning(
            "Detailed feedback analysis failed",
            extra={
                "component": "feedback_collector",
                "repo": repo,
                "duration_seconds": round(elapsed_time, 2),
                "error_type": type(exc).__name__,
                "error_message": str(exc),
                "status": "failed"
            },
            exc_info=True
        )
        console.print(
            f"[warning]Warning: Detailed feedback analysis failed: {exc}", style="warning"
        )

        # Provide actionable guidance based on exception type
        if isinstance(exc, requests.RequestException):
            console.print(
                "[cyan]💡 해결 방법: 네트워크 연결을 확인하거나 LLM endpoint 설정을 검토하세요.",
                style="cyan"
            )
            console.print(
                "[dim]  설정 확인: gfa config show",
                style="dim"
            )
        elif isinstance(exc, json.JSONDecodeError):
            console.print(
                "[cyan]💡 해결 방법: LLM 응답 형식이 올바르지 않습니다. 모델 설정을 확인하세요.",
                style="cyan"
            )
            console.print(
                "[dim]  다른 모델을 시도하거나 config.llm.model을 확인하세요.",
                style="dim"
            )
        elif isinstance(exc, (ValueError, KeyError)):
            console.print(
                "[cyan]💡 해결 방법: 수집된 데이터 형식에 문제가 있습니다.",
                style="cyan"
            )
            console.print(
                "[dim]  --debug 플래그로 상세 로그를 확인하거나 이슈를 제출해주세요.",
                style="dim"
            )

        console.print("[cyan]Continuing with standard analysis...", style="cyan")
        return None
    except KeyboardInterrupt:
        console.print("\n[warning]Analysis interrupted by user", style="warning")
        raise


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
    metrics_path = persist_metrics(output_dir=output_dir, metrics_data=metrics_payload)
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


def _check_repository_activity(
    collection: CollectionResult, repo_input: str, months: int
) -> None:
    """Check if repository has any activity and exit if not.

    Args:
        collection: Collection result to check
        repo_input: Repository name
        months: Number of months analyzed

    Raises:
        typer.Exit: If no activity is found
    """
    if not collection.has_activity():
        console.print("[warning]No activity found in the repository for the specified period.[/]")
        console.print(f"[info]Repository:[/] {repo_input}")
        console.print(f"[info]Period:[/] Last {months} months")
        console.print("[info]Suggestions:[/]")
        console.print("  • Try increasing the analysis period: [accent]gfa init --months 24[/]")
        console.print("  • Verify the repository has commits, PRs, or issues")
        console.print("  • Check if your PAT has access to this repository")
        raise typer.Exit(code=1)


def _collect_yearend_data(
    collector: Collector,
    repo_input: str,
    since: datetime,
    filters: AnalysisFilters,
    author: Optional[str] = None,
) -> tuple[Optional[Any], Optional[Any], Optional[Any]]:
    """Collect year-end review data in parallel.

    Args:
        collector: Data collector instance
        repo_input: Repository name
        since: Start date for data collection
        filters: Analysis filters
        author: Optional GitHub username to filter by author

    Returns:
        Tuple of (monthly_trends_data, tech_stack_data, collaboration_data)
    """
    console.print("[accent]Collecting year-end review data in parallel...", style="accent")

    # Get PR metadata once for reuse
    _, pr_metadata = collector.list_pull_requests(repo_input, since, filters, author)

    yearend_tasks = {
        "monthly_trends": (
            collector.collect_monthly_trends,
            (repo_input, since, filters),
            "monthly trends"
        ),
        "tech_stack": (
            collector.collect_tech_stack,
            (repo_input, pr_metadata),
            "tech stack"
        ),
        "collaboration": (
            collector.collect_collaboration_network,
            (repo_input, pr_metadata, filters),
            "collaboration network"
        ),
    }

    # Use common parallel task runner
    yearend_data = run_parallel_tasks(
        tasks=yearend_tasks,
        max_workers=PARALLEL_CONFIG['max_workers_yearend'],
        timeout=PARALLEL_CONFIG['yearend_timeout'],
        task_type="collection"
    )

    # Convert empty lists to None for consistency with downstream code
    return (
        yearend_data.get("monthly_trends") or None,
        yearend_data.get("tech_stack") or None,
        yearend_data.get("collaboration") or None,
    )


def _resolve_output_dir(value: Path | str | object) -> Path:
    """Normalise CLI path inputs for both Typer and direct function calls."""

    if isinstance(value, Path):
        return value.expanduser()

    default_candidate = getattr(value, "default", value)
    if isinstance(default_candidate, Path):
        return default_candidate.expanduser()

    return Path(str(default_candidate)).expanduser()


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

    review_results = run_parallel_tasks(
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
    output_dir_resolved = _resolve_output_dir(output_dir)
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
    import re

    lines = ["## 🎯 한눈에 보기 (Executive Summary)", ""]
    lines.append("> 핵심 성과와 개선 포인트를 빠르게 파악하세요")
    lines.append("")

    # Extract key achievements from brief (awards section)
    awards_section = _extract_section_content(brief_content, "## 🏆 Awards Cabinet")
    if awards_section:
        # Count total awards
        award_matches = re.findall(r'\|\s*[^|]+\s*\|\s*([^|]+)\s*\|', awards_section)
        total_awards = len([m for m in award_matches if m.strip() and m.strip() not in ['어워드', '-----']])
        if total_awards > 0:
            lines.append(f"**🏆 획득 어워드**: {total_awards}개")

    # Extract highlights from brief
    highlights_section = _extract_section_content(brief_content, "## ✨ Growth Highlights")
    if highlights_section:
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


def _get_authenticated_user(collector: Collector) -> str:
    """Authenticate and get the current GitHub user.

    Args:
        collector: Collector instance for authentication

    Returns:
        GitHub username of authenticated user

    Raises:
        typer.Exit: If authentication fails
    """
    console.print()
    console.rule("Phase 0: Authentication")
    with console.status("[accent]Retrieving authenticated user...", spinner="dots"):
        try:
            author = collector.get_authenticated_user()
            console.print(f"[success]✓ Authenticated as: {author}[/]")
            return author
        except (ValueError, PermissionError) as exc:
            console.print(f"[error]Failed to get authenticated user: {exc}[/]")
            raise typer.Exit(code=1) from exc


def _collect_personal_activity(
    collector: Collector,
    repo_input: str,
    months: int,
    filters: AnalysisFilters,
    author: str,
):
    """Collect personal activity data for a repository.

    Args:
        collector: Collector instance
        repo_input: Repository name
        months: Number of months to collect
        filters: Analysis filters
        author: GitHub username

    Returns:
        Collection result

    Raises:
        typer.Exit: If no activity found
    """
    console.print()
    console.rule("Phase 1: Personal Activity Collection")
    console.print(f"[accent]Collecting personal activity for {author}...[/]")
    with console.status("[accent]Collecting repository data...", spinner="bouncingBar"):
        collection = collector.collect(repo=repo_input, months=months, filters=filters, author=author)

    _check_repository_activity(collection, repo_input, months)
    return collection


def _compute_and_display_metrics(
    analyzer: Analyzer,
    collection,
    detailed_feedback_snapshot: Optional[DetailedFeedbackSnapshot],
    monthly_trends_data,
    tech_stack_data,
    collaboration_data,
) -> MetricSnapshot:
    """Compute metrics and display summary.

    Args:
        analyzer: Analyzer instance
        collection: Collection result
        detailed_feedback_snapshot: Detailed feedback data
        monthly_trends_data: Monthly trends data
        tech_stack_data: Tech stack data
        collaboration_data: Collaboration data

    Returns:
        Computed metrics snapshot
    """
    console.print()
    console.rule("Phase 3: Metrics Computation")
    with console.status("[accent]Synthesizing insights...", spinner="dots"):
        metrics = analyzer.compute_metrics(
            collection,
            detailed_feedback=detailed_feedback_snapshot,
            monthly_trends_data=monthly_trends_data,
            tech_stack_data=tech_stack_data,
            collaboration_data=collaboration_data,
        )
    console.print("[success]✓ Metrics computed successfully[/]")

    console.print()
    console.rule("Analysis Summary")
    render_metrics(metrics)

    return metrics


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
    metrics_payload = prepare_metrics_payload(metrics)
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
