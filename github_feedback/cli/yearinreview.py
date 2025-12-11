"""Year-in-review analysis functionality for CLI."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from ..analyzer import Analyzer
from ..collectors.collector import Collector
from ..core.config import Config
from ..core.console import Console
from ..core.models import AnalysisFilters
from ..year_in_review.models import RepositoryAnalysis

console = Console()


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


def _load_personal_development_data(
    reviews_dir: Path,
) -> tuple[list, list, list]:
    """Load personal development data from personal_development.json.

    Args:
        reviews_dir: Reviews directory for the repository

    Returns:
        Tuple of (strengths, improvements, growth_indicators)
    """
    personal_dev_path = reviews_dir / "personal_development.json"

    strengths = []
    improvements = []
    growth_indicators = []

    if personal_dev_path.exists():
        with open(personal_dev_path, "r", encoding="utf-8") as f:
            personal_dev = json.load(f)

        strengths = personal_dev.get("strengths", [])
        improvements = personal_dev.get("improvement_areas", [])
        growth_indicators = personal_dev.get("growth_indicators", [])

    return strengths, improvements, growth_indicators


def _load_communication_skills_data(
    output_dir: Path, repo_name: str
) -> tuple[Optional[float], Optional[float], Optional[float], Optional[float], dict, dict, dict, dict]:
    """Load communication skills data from metrics.json.

    Args:
        output_dir: Output directory
        repo_name: Repository name

    Returns:
        Tuple of (commit_message_quality, pr_title_quality, review_tone_quality,
                  issue_quality, commit_stats, pr_title_stats, review_tone_stats, issue_stats)
    """
    commit_message_quality = None
    pr_title_quality = None
    review_tone_quality = None
    issue_quality = None
    commit_stats = {}
    pr_title_stats = {}
    review_tone_stats = {}
    issue_stats = {}

    metrics_path = _get_year_in_review_metrics_path(output_dir, repo_name)
    legacy_metrics_path = _get_legacy_year_in_review_metrics_path(output_dir, repo_name)
    metrics_data, _ = _load_year_in_review_metrics_data(metrics_path, legacy_metrics_path)

    if metrics_data:
        try:
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

    return (
        commit_message_quality,
        pr_title_quality,
        review_tone_quality,
        issue_quality,
        commit_stats,
        pr_title_stats,
        review_tone_stats,
        issue_stats,
    )


def _collect_tech_stack_data(
    collector: Collector,
    repo_name: str,
    year: int,
    filters: AnalysisFilters,
) -> dict:
    """Collect tech stack data for repository.

    Args:
        collector: Collector instance
        repo_name: Repository name
        year: Year being analyzed
        filters: Analysis filters

    Returns:
        Dictionary of tech stack data (language -> count)
    """
    tech_stack = {}

    try:
        # Use a much broader time window to get sufficient data for tech stack analysis
        # Instead of only PRs created in the target year, analyze recent repository activity
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

    return tech_stack


def _collect_commit_counts(
    collector: Collector,
    repo_name: str,
    author: str,
    year: int,
) -> tuple[int, int]:
    """Collect total and yearly commit counts.

    Args:
        collector: Collector instance
        repo_name: Repository name
        author: GitHub username
        year: Year being analyzed

    Returns:
        Tuple of (total_commits, year_commits_count)
    """
    owner, repo = repo_name.split("/", 1)

    # Get total commit count
    all_commits = collector.api_client.get_user_commits_in_repo(
        owner, repo, author, max_pages=10
    )
    total_commits = len(all_commits)

    # Get commits in the year
    since = datetime(year, 1, 1)
    until = datetime(year, 12, 31, 23, 59, 59)

    year_commits_params = {
        "author": author,
        "since": since.isoformat() + "Z",
        "until": until.isoformat() + "Z",
    }
    year_commits = collector.api_client.request_all(
        f"/repos/{owner}/{repo}/commits",
        params=year_commits_params,
    )

    return total_commits, len(year_commits)


def _save_detailed_feedback_to_metrics(
    output_dir: Path,
    repo_name: str,
    detailed_feedback_snapshot,
) -> None:
    """Save detailed feedback snapshot to metrics.json.

    Args:
        output_dir: Output directory
        repo_name: Repository name
        detailed_feedback_snapshot: DetailedFeedbackSnapshot object
    """
    if not detailed_feedback_snapshot:
        return

    console.print(f"[dim]💾 Saving detailed feedback to metrics.json...[/]")
    metrics_path = _get_year_in_review_metrics_path(output_dir, repo_name)
    legacy_metrics_path = _get_legacy_year_in_review_metrics_path(output_dir, repo_name)
    from ..core.utils import FileSystemManager

    metrics_dir = metrics_path.parent
    FileSystemManager.ensure_directory(metrics_dir)

    metrics_data, loaded_from_legacy = _load_year_in_review_metrics_data(
        metrics_path, legacy_metrics_path
    )

    # Add detailed_feedback to metrics
    metrics_data["detailed_feedback"] = detailed_feedback_snapshot.to_dict()

    # Save updated metrics
    with metrics_path.open("w", encoding="utf-8") as f:
        json.dump(metrics_data, f, indent=2, ensure_ascii=False)

    if loaded_from_legacy:
        _cleanup_legacy_metrics_path(legacy_metrics_path)

    console.print(f"[success]✅ Saved detailed feedback to {metrics_path}[/]")


def analyze_single_repository_for_year_review(
    config: Config,
    repo_name: str,
    year: int,
    output_dir: Path,
    run_feedback_analysis_func,
    collect_detailed_feedback_func,
) -> Optional[RepositoryAnalysis]:
    """Analyze a single repository for year-in-review.

    Args:
        config: Configuration object
        repo_name: Repository name (owner/repo)
        year: Year being analyzed
        output_dir: Output directory
        run_feedback_analysis_func: Function to run feedback analysis
        collect_detailed_feedback_func: Function to collect detailed feedback

    Returns:
        RepositoryAnalysis object or None if analysis fails
    """
    try:
        # Initialize components
        collector = Collector(config)
        author = collector.get_authenticated_user()
        safe_repo = repo_name.replace("/", "__")
        analyzer = Analyzer(web_base_url=config.server.web_url)

        # Calculate year date range
        since = datetime(year, 1, 1)
        until = datetime(year, 12, 31, 23, 59, 59)

        # Set up filters
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
        feedback_report_path, pr_results = run_feedback_analysis_func(
            config=config,
            repo_input=repo_name,
            output_dir=output_dir,
        )

        # Collect detailed feedback for communication skills analysis
        console.print(f"[dim]📊 Collecting detailed feedback for {repo_name}...[/]")
        detailed_feedback_snapshot = collect_detailed_feedback_func(
            collector=collector,
            analyzer=analyzer,
            config=config,
            repo=repo_name,
            since=since,
            filters=filters,
            author=author,
        )

        # Save detailed feedback to metrics.json
        _save_detailed_feedback_to_metrics(output_dir, repo_name, detailed_feedback_snapshot)

        # Load personal development data
        reviews_dir = output_dir / "reviews" / safe_repo
        strengths, improvements, growth_indicators = _load_personal_development_data(reviews_dir)

        # Load communication skills data from metrics.json
        (
            commit_message_quality,
            pr_title_quality,
            review_tone_quality,
            issue_quality,
            commit_stats,
            pr_title_stats,
            review_tone_stats,
            issue_stats,
        ) = _load_communication_skills_data(output_dir, repo_name)

        # Collect tech stack data
        tech_stack = _collect_tech_stack_data(collector, repo_name, year, filters)

        # Get commit counts
        total_commits, year_commits_count = _collect_commit_counts(
            collector, repo_name, author, year
        )

        # Get personal development path
        personal_dev_path = reviews_dir / "personal_development.json"

        return RepositoryAnalysis(
            full_name=repo_name,
            pr_count=len(pr_results),
            commit_count=total_commits,
            year_commits=year_commits_count,
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
