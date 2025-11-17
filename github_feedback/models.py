"""Domain models shared across the GitHub feedback toolkit."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from .retrospective import RetrospectiveSnapshot


@dataclass(slots=True)
class ReviewPoint:
    """Single highlight used when summarising pull requests."""

    message: str
    example: Optional[str] = None

    def to_dict(self) -> Dict[str, Optional[str]]:
        """Serialise the review point for JSON persistence."""

        payload: Dict[str, Optional[str]] = {"message": self.message}
        if self.example:
            payload["example"] = self.example
        return payload


@dataclass(slots=True)
class ReviewSummary:
    """Structured response returned from LLM powered reviews."""

    overview: str
    strengths: List[ReviewPoint] = field(default_factory=list)
    improvements: List[ReviewPoint] = field(default_factory=list)

    def to_dict(self) -> Dict[str, object]:
        """Convert the summary into a JSON friendly payload."""

        return {
            "overview": self.overview,
            "strengths": [point.to_dict() for point in self.strengths],
            "improvements": [point.to_dict() for point in self.improvements],
        }


@dataclass(slots=True)
class PullRequestFile:
    """Individual file diff captured when reviewing a pull request."""

    filename: str
    status: str
    additions: int
    deletions: int
    changes: int
    patch: Optional[str] = None

    def to_dict(self) -> Dict[str, object]:
        """Serialise the file metadata for persistence."""

        payload: Dict[str, object] = {
            "filename": self.filename,
            "status": self.status,
            "additions": self.additions,
            "deletions": self.deletions,
            "changes": self.changes,
        }
        if self.patch is not None:
            payload["patch"] = self.patch
        return payload


@dataclass(slots=True)
class PullRequestReviewBundle:
    """Complete snapshot of a pull request for LLM reviews."""

    repo: str
    number: int
    title: str
    body: str
    author: str
    html_url: str
    created_at: datetime
    updated_at: datetime
    additions: int
    deletions: int
    changed_files: int
    review_bodies: List[str]
    review_comments: List[str]
    files: List[PullRequestFile]

    def to_dict(self) -> Dict[str, object]:
        """Convert the bundle into a JSON serialisable structure."""

        return {
            "repo": self.repo,
            "number": self.number,
            "title": self.title,
            "body": self.body,
            "author": self.author,
            "html_url": self.html_url,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "additions": self.additions,
            "deletions": self.deletions,
            "changed_files": self.changed_files,
            "review_bodies": self.review_bodies,
            "review_comments": self.review_comments,
            "files": [file.to_dict() for file in self.files],
        }


@dataclass(slots=True)
class PullRequestSummary:
    """Lightweight snapshot of a pull request for reporting."""

    number: int
    title: str
    author: str
    html_url: str
    created_at: datetime
    merged_at: Optional[datetime]
    additions: int = 0
    deletions: int = 0

    def to_dict(self) -> Dict[str, object]:
        """Serialise the summary for JSON persistence."""

        payload: Dict[str, object] = {
            "number": self.number,
            "title": self.title,
            "author": self.author,
            "html_url": self.html_url,
            "created_at": self.created_at.isoformat(),
            "additions": self.additions,
            "deletions": self.deletions,
        }
        if self.merged_at is not None:
            payload["merged_at"] = self.merged_at.isoformat()
        return payload


class AnalysisStatus(str, Enum):
    """Lifecycle marker for analysis runs."""

    CREATED = "created"
    COLLECTED = "collected"
    ANALYSED = "analysed"
    REPORTED = "reported"


@dataclass(slots=True)
class AnalysisFilters:
    """Filters controlling which repository artefacts are collected."""

    include_branches: List[str] = field(default_factory=list)
    exclude_branches: List[str] = field(default_factory=list)
    include_paths: List[str] = field(default_factory=list)
    exclude_paths: List[str] = field(default_factory=list)
    include_languages: List[str] = field(default_factory=list)
    exclude_bots: bool = True

    def is_empty(self) -> bool:
        """Check if all filter lists are empty.

        Returns:
            True if no filters are applied (all lists are empty), False otherwise.
        """
        return (
            not self.include_branches and
            not self.exclude_branches and
            not self.include_paths and
            not self.exclude_paths and
            not self.include_languages
        )


@dataclass(slots=True)
class CollectionResult:
    """Summary of the raw artefacts collected from GitHub."""

    repo: str
    months: int
    collected_at: datetime
    commits: int
    pull_requests: int
    reviews: int
    issues: int
    filters: AnalysisFilters
    pull_request_examples: List[PullRequestSummary] = field(default_factory=list)
    since_date: Optional[datetime] = None  # Actual analysis start date
    until_date: Optional[datetime] = None  # Actual analysis end date

    def has_activity(self) -> bool:
        """Check if the collection has any significant activity.

        Returns:
            True if there are any commits, pull requests, reviews, or issues, False otherwise.
        """
        return (
            self.commits > 0 or
            self.pull_requests > 0 or
            self.reviews > 0 or
            self.issues > 0
        )


@dataclass(slots=True)
class CommitMessageFeedback:
    """Analysis of commit message quality."""

    total_commits: int
    good_messages: int
    poor_messages: int
    suggestions: List[str] = field(default_factory=list)
    examples_good: List[Dict[str, str]] = field(default_factory=list)
    examples_poor: List[Dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, object]:
        """Serialise commit message feedback."""
        return {
            "total_commits": self.total_commits,
            "good_messages": self.good_messages,
            "poor_messages": self.poor_messages,
            "suggestions": self.suggestions,
            "examples_good": self.examples_good,
            "examples_poor": self.examples_poor,
        }


@dataclass(slots=True)
class PRTitleFeedback:
    """Analysis of pull request title quality."""

    total_prs: int
    clear_titles: int
    vague_titles: int
    suggestions: List[str] = field(default_factory=list)
    examples_good: List[Dict[str, str]] = field(default_factory=list)
    examples_poor: List[Dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, object]:
        """Serialise PR title feedback."""
        return {
            "total_prs": self.total_prs,
            "clear_titles": self.clear_titles,
            "vague_titles": self.vague_titles,
            "suggestions": self.suggestions,
            "examples_good": self.examples_good,
            "examples_poor": self.examples_poor,
        }


@dataclass(slots=True)
class ReviewToneFeedback:
    """Analysis of code review tone and style."""

    total_reviews: int
    constructive_reviews: int
    harsh_reviews: int
    neutral_reviews: int
    suggestions: List[str] = field(default_factory=list)
    examples_good: List[Dict[str, str]] = field(default_factory=list)
    examples_improve: List[Dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, object]:
        """Serialise review tone feedback."""
        return {
            "total_reviews": self.total_reviews,
            "constructive_reviews": self.constructive_reviews,
            "harsh_reviews": self.harsh_reviews,
            "neutral_reviews": self.neutral_reviews,
            "suggestions": self.suggestions,
            "examples_good": self.examples_good,
            "examples_improve": self.examples_improve,
        }


@dataclass(slots=True)
class IssueFeedback:
    """Analysis of issue quality and clarity."""

    total_issues: int
    well_described: int
    poorly_described: int
    suggestions: List[str] = field(default_factory=list)
    examples_good: List[Dict[str, str]] = field(default_factory=list)
    examples_poor: List[Dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, object]:
        """Serialise issue feedback."""
        return {
            "total_issues": self.total_issues,
            "well_described": self.well_described,
            "poorly_described": self.poorly_described,
            "suggestions": self.suggestions,
            "examples_good": self.examples_good,
            "examples_poor": self.examples_poor,
        }


@dataclass(slots=True)
class DetailedFeedbackSnapshot:
    """Comprehensive feedback including commit messages, PR titles, review tone, issues, and personal development."""

    commit_feedback: Optional[CommitMessageFeedback] = None
    pr_title_feedback: Optional[PRTitleFeedback] = None
    review_tone_feedback: Optional[ReviewToneFeedback] = None
    issue_feedback: Optional[IssueFeedback] = None
    personal_development: Optional[PersonalDevelopmentAnalysis] = None

    def to_dict(self) -> Dict[str, object]:
        """Serialise detailed feedback."""
        result: Dict[str, object] = {}
        if self.commit_feedback:
            result["commit_feedback"] = self.commit_feedback.to_dict()
        if self.pr_title_feedback:
            result["pr_title_feedback"] = self.pr_title_feedback.to_dict()
        if self.review_tone_feedback:
            result["review_tone_feedback"] = self.review_tone_feedback.to_dict()
        if self.issue_feedback:
            result["issue_feedback"] = self.issue_feedback.to_dict()
        if self.personal_development:
            result["personal_development"] = self.personal_development.to_dict()
        return result


@dataclass(slots=True)
class MonthlyTrend:
    """Monthly activity trend data."""

    month: str  # YYYY-MM format
    commits: int = 0
    pull_requests: int = 0
    reviews: int = 0
    issues: int = 0

    def to_dict(self) -> Dict[str, object]:
        """Serialise monthly trend."""
        return {
            "month": self.month,
            "commits": self.commits,
            "pull_requests": self.pull_requests,
            "reviews": self.reviews,
            "issues": self.issues,
        }


@dataclass(slots=True)
class MonthlyTrendInsights:
    """Insights derived from monthly trend analysis."""

    peak_month: Optional[str] = None  # Month with highest activity
    quiet_month: Optional[str] = None  # Month with lowest activity
    trend_direction: str = "stable"  # "increasing", "decreasing", "stable"
    total_active_months: int = 0  # Number of months with activity
    consistency_score: float = 0.0  # 0-1 scale
    insights: List[str] = field(default_factory=list)  # Human-readable insights

    def to_dict(self) -> Dict[str, object]:
        """Serialise monthly trend insights."""
        return {
            "peak_month": self.peak_month,
            "quiet_month": self.quiet_month,
            "trend_direction": self.trend_direction,
            "total_active_months": self.total_active_months,
            "consistency_score": self.consistency_score,
            "insights": self.insights,
        }


@dataclass(slots=True)
class TechStackAnalysis:
    """Analysis of technologies used in the codebase."""

    languages: Dict[str, int] = field(default_factory=dict)  # language -> file count
    top_languages: List[str] = field(default_factory=list)  # Top 5 languages
    diversity_score: float = 0.0  # 0-1 scale

    def to_dict(self) -> Dict[str, object]:
        """Serialise tech stack analysis."""
        return {
            "languages": self.languages,
            "top_languages": self.top_languages,
            "diversity_score": self.diversity_score,
        }


@dataclass(slots=True)
class CollaborationNetwork:
    """Analysis of collaboration patterns."""

    pr_reviewers: Dict[str, int] = field(default_factory=dict)  # reviewer -> count
    top_reviewers: List[str] = field(default_factory=list)  # Top 5 reviewers
    review_received_count: int = 0  # Number of reviews received
    unique_collaborators: int = 0  # Number of unique collaborators

    def to_dict(self) -> Dict[str, object]:
        """Serialise collaboration network."""
        return {
            "pr_reviewers": self.pr_reviewers,
            "top_reviewers": self.top_reviewers,
            "review_received_count": self.review_received_count,
            "unique_collaborators": self.unique_collaborators,
        }


@dataclass(slots=True)
class YearEndReview:
    """Year-end specific insights and reflections."""

    proudest_moments: List[str] = field(default_factory=list)
    biggest_challenges: List[str] = field(default_factory=list)
    lessons_learned: List[str] = field(default_factory=list)
    next_year_goals: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, object]:
        """Serialise year-end review."""
        return {
            "proudest_moments": self.proudest_moments,
            "biggest_challenges": self.biggest_challenges,
            "lessons_learned": self.lessons_learned,
            "next_year_goals": self.next_year_goals,
        }


@dataclass(slots=True)
class StrengthPoint:
    """Individual strength with concrete evidence."""

    category: str  # e.g., "코드 품질", "문제 해결", "협업", "기술 역량"
    description: str
    evidence: List[str] = field(default_factory=list)  # Concrete examples from PRs
    impact: str = "medium"  # "high", "medium", "low"

    def to_dict(self) -> Dict[str, object]:
        """Serialise strength point."""
        return {
            "category": self.category,
            "description": self.description,
            "evidence": self.evidence,
            "impact": self.impact,
        }


@dataclass(slots=True)
class ImprovementArea:
    """Area for improvement with actionable suggestions."""

    category: str  # e.g., "코드 리뷰", "테스트", "문서화", "성능"
    description: str
    evidence: List[str] = field(default_factory=list)  # Specific examples
    suggestions: List[str] = field(default_factory=list)  # Actionable recommendations
    priority: str = "medium"  # "critical", "important", "nice-to-have"

    def to_dict(self) -> Dict[str, object]:
        """Serialise improvement area."""
        return {
            "category": self.category,
            "description": self.description,
            "evidence": self.evidence,
            "suggestions": self.suggestions,
            "priority": self.priority,
        }


@dataclass(slots=True)
class GrowthIndicator:
    """Indicator of growth over time."""

    aspect: str  # e.g., "코드 복잡도 관리", "리뷰 품질", "커뮤니케이션"
    description: str
    before_examples: List[str] = field(default_factory=list)  # Early PR examples
    after_examples: List[str] = field(default_factory=list)  # Recent PR examples
    progress_summary: str = ""  # Summary of improvement

    def to_dict(self) -> Dict[str, object]:
        """Serialise growth indicator."""
        return {
            "aspect": self.aspect,
            "description": self.description,
            "before_examples": self.before_examples,
            "after_examples": self.after_examples,
            "progress_summary": self.progress_summary,
        }


@dataclass(slots=True)
class PersonalDevelopmentAnalysis:
    """Comprehensive analysis of personal strengths, areas for improvement, and growth."""

    strengths: List[StrengthPoint] = field(default_factory=list)
    improvement_areas: List[ImprovementArea] = field(default_factory=list)
    growth_indicators: List[GrowthIndicator] = field(default_factory=list)
    overall_assessment: str = ""
    key_achievements: List[str] = field(default_factory=list)
    next_focus_areas: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, object]:
        """Serialise personal development analysis."""
        return {
            "strengths": [s.to_dict() for s in self.strengths],
            "improvement_areas": [i.to_dict() for i in self.improvement_areas],
            "growth_indicators": [g.to_dict() for g in self.growth_indicators],
            "overall_assessment": self.overall_assessment,
            "key_achievements": self.key_achievements,
            "next_focus_areas": self.next_focus_areas,
        }


@dataclass(slots=True)
class MetricSnapshot:
    """Computed metrics ready for reporting."""

    repo: str
    months: int
    generated_at: datetime
    status: AnalysisStatus
    summary: Dict[str, str]
    stats: Dict[str, Dict[str, float]]
    evidence: Dict[str, List[str]]
    highlights: List[str] = field(default_factory=list)
    spotlight_examples: Dict[str, List[str]] = field(default_factory=dict)
    yearbook_story: List[str] = field(default_factory=list)
    awards: List[str] = field(default_factory=list)
    detailed_feedback: Optional[DetailedFeedbackSnapshot] = None
    monthly_trends: List[MonthlyTrend] = field(default_factory=list)
    monthly_insights: Optional[MonthlyTrendInsights] = None
    tech_stack: Optional[TechStackAnalysis] = None
    collaboration: Optional[CollaborationNetwork] = None
    year_end_review: Optional[YearEndReview] = None
    retrospective: Optional[RetrospectiveSnapshot] = None  # For deep analysis
    since_date: Optional[datetime] = None  # Actual analysis start date
    until_date: Optional[datetime] = None  # Actual analysis end date
