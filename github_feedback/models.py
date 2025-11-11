"""Domain models shared across the GitHub feedback toolkit."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional


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
class PromptRequest:
    """Reusable prompt instructions for LLM powered annual feedback."""

    identifier: str
    title: str
    instructions: str
    prompt: str

    def to_dict(self) -> Dict[str, str]:
        """Serialise the prompt request for persistence or inspection."""

        return {
            "identifier": self.identifier,
            "title": self.title,
            "instructions": self.instructions,
            "prompt": self.prompt,
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
    """Comprehensive feedback including commit messages, PR titles, review tone, and issues."""

    commit_feedback: Optional[CommitMessageFeedback] = None
    pr_title_feedback: Optional[PRTitleFeedback] = None
    review_tone_feedback: Optional[ReviewToneFeedback] = None
    issue_feedback: Optional[IssueFeedback] = None

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
class ReflectionPrompts:
    """Self-reflection questions for year-end review."""

    questions: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, object]:
        """Serialise reflection prompts."""
        return {
            "questions": self.questions,
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
    reflection_prompts: Optional[ReflectionPrompts] = None
    year_end_review: Optional[YearEndReview] = None
    since_date: Optional[datetime] = None  # Actual analysis start date
    until_date: Optional[datetime] = None  # Actual analysis end date
