"""Data collection utilities for CLI."""

from __future__ import annotations

import json
import logging
import time
from datetime import datetime
from typing import Any, Optional

import requests
import typer

from ..analyzer import Analyzer
from ..collectors.collector import Collector
from ..core.config import Config
from ..core.console import Console
from ..core.constants import (
    COLLECTION_LIMITS,
    PARALLEL_CONFIG,
    TaskType,
)
from ..llm.client import LLMClient
from ..core.models import AnalysisFilters, DetailedFeedbackSnapshot

# Import helper functions from cli_helpers
from .helpers import run_parallel_tasks, validate_collected_data

console = Console()
logger = logging.getLogger(__name__)


def collect_detailed_feedback(
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


def check_repository_activity(
    collection, repo_input: str, months: int
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


def collect_yearend_data(
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


def collect_personal_activity(
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

    check_repository_activity(collection, repo_input, months)
    return collection
