"""Type definitions for GitHub API responses.

This module provides TypedDict definitions for GitHub API responses
to improve type safety and IDE support.
"""

from typing import TypedDict, NotRequired, List


class GitHubUser(TypedDict):
    """GitHub user object."""

    login: str
    id: int
    node_id: str
    avatar_url: str
    type: str
    site_admin: bool


class GitHubRepository(TypedDict):
    """GitHub repository object."""

    id: int
    node_id: str
    name: str
    full_name: str
    private: bool
    owner: GitHubUser
    html_url: str
    description: NotRequired[str]
    fork: bool
    url: str
    created_at: str
    updated_at: str
    pushed_at: str
    git_url: str
    ssh_url: str
    clone_url: str
    size: int
    stargazers_count: int
    watchers_count: int
    language: NotRequired[str]
    has_issues: bool
    has_projects: bool
    has_downloads: bool
    has_wiki: bool
    has_pages: bool
    forks_count: int
    open_issues_count: int
    default_branch: str


class GitHubCommit(TypedDict):
    """GitHub commit object."""

    sha: str
    node_id: str
    commit: "GitHubCommitDetail"
    url: str
    html_url: str
    author: NotRequired[GitHubUser]
    committer: NotRequired[GitHubUser]


class GitHubCommitDetail(TypedDict):
    """GitHub commit detail object."""

    author: "GitHubCommitAuthor"
    committer: "GitHubCommitAuthor"
    message: str
    tree: "GitHubTree"
    url: str


class GitHubCommitAuthor(TypedDict):
    """GitHub commit author object."""

    name: str
    email: str
    date: str


class GitHubTree(TypedDict):
    """GitHub tree object."""

    sha: str
    url: str


class GitHubPullRequest(TypedDict):
    """GitHub pull request object."""

    id: int
    node_id: str
    number: int
    state: str
    locked: bool
    title: str
    user: GitHubUser
    body: NotRequired[str]
    created_at: str
    updated_at: str
    closed_at: NotRequired[str]
    merged_at: NotRequired[str]
    merge_commit_sha: NotRequired[str]
    assignee: NotRequired[GitHubUser]
    assignees: List[GitHubUser]
    draft: bool
    head: "GitHubPullRequestRef"
    base: "GitHubPullRequestRef"
    html_url: str
    url: str
    additions: NotRequired[int]
    deletions: NotRequired[int]
    changed_files: NotRequired[int]


class GitHubPullRequestRef(TypedDict):
    """GitHub pull request ref object."""

    label: str
    ref: str
    sha: str
    user: GitHubUser
    repo: GitHubRepository


class GitHubIssue(TypedDict):
    """GitHub issue object."""

    id: int
    node_id: str
    number: int
    title: str
    user: GitHubUser
    labels: List["GitHubLabel"]
    state: str
    locked: bool
    assignee: NotRequired[GitHubUser]
    assignees: List[GitHubUser]
    comments: int
    created_at: str
    updated_at: str
    closed_at: NotRequired[str]
    body: NotRequired[str]
    html_url: str
    url: str


class GitHubLabel(TypedDict):
    """GitHub label object."""

    id: int
    node_id: str
    url: str
    name: str
    color: str
    default: bool
    description: NotRequired[str]


class GitHubReviewComment(TypedDict):
    """GitHub review comment object."""

    id: int
    node_id: str
    pull_request_review_id: int
    path: str
    position: NotRequired[int]
    original_position: int
    commit_id: str
    original_commit_id: str
    user: GitHubUser
    body: str
    created_at: str
    updated_at: str
    html_url: str
    url: str
    line: NotRequired[int]
    side: NotRequired[str]


class GitHubPullRequestFile(TypedDict):
    """GitHub pull request file object."""

    sha: str
    filename: str
    status: str
    additions: int
    deletions: int
    changes: int
    blob_url: str
    raw_url: str
    contents_url: str
    patch: NotRequired[str]
