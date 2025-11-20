"""Year-in-review workflow helper functions for GitHub analysis.

This module contains helper functions for running year-in-review analysis,
collecting repository metrics, and generating comprehensive year-end reports
across multiple repositories.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import typer

from ...analyzer import Analyzer
from ...collector import Collector
from ...config import Config
from ...console import Console
from ...constants import TaskType
from ...models import AnalysisFilters
from ...utils import FileSystemManager
from ...year_in_review_reporter import YearInReviewReporter, RepositoryAnalysis
from ..ui.display import render_metrics
from ..utils.output_utils import resolve_output_dir
from ..utils.parallel import run_parallel_tasks
from .feedback_workflow import _run_feedback_analysis, _collect_detailed_feedback, _get_authenticated_user


console = Console()


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
    from ...year_in_review_reporter import YearInReviewReporter, RepositoryAnalysis

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
    author = _get_authenticated_user(collector)

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

    output_dir_resolved = resolve_output_dir(output_dir)

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
    analysis_results = run_parallel_tasks(
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
    from ...year_in_review_reporter import RepositoryAnalysis

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
        detailed_feedback_snapshot = _collect_detailed_feedback(
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
            from ...utils import FileSystemManager

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
