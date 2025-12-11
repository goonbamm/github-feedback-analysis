"""Feedback section builder."""

import html
from typing import Any, Callable, Dict, List, Optional, Union

from ..core.constants import DISPLAY_LIMITS
from ..game_elements import GameRenderer
from ..core.models import (
    CommitMessageFeedback,
    IssueFeedback,
    MetricSnapshot,
    PRTitleFeedback,
    ReviewToneFeedback,
)
from ..section_builders.base_builder import SectionBuilder

# Type alias for feedback data structures
FeedbackData = Union[CommitMessageFeedback, PRTitleFeedback, ReviewToneFeedback, IssueFeedback]


def _escape_table_cell(text: str) -> str:
    """Escape special characters in markdown table cells to prevent table breakage.

    Args:
        text: Text to escape

    Returns:
        Escaped text safe for use in markdown tables
    """
    if text is None:
        return ""

    text = html.escape(str(text), quote=False)

    # Replace pipe characters that would break table structure
    text = text.replace("|", "\\|")

    # Replace newlines with HTML breaks for multi-line content
    text = text.replace("\n", "<br>")

    # Trim excessive whitespace
    text = " ".join(text.split())

    return text


class FeedbackBuilder(SectionBuilder):
    """Builder for detailed feedback section."""

    def __init__(self, metrics: MetricSnapshot, web_url: str = "https://github.com"):
        """Initialize feedback builder.

        Args:
            metrics: MetricSnapshot containing all analysis data
            web_url: Base URL for GitHub links (default: https://github.com)
        """
        super().__init__(metrics)
        self.web_url = web_url

    def build(self) -> List[str]:
        """Build detailed feedback section.

        Returns:
            List of markdown lines for feedback section
        """
        if not self.metrics.detailed_feedback:
            return []

        feedback = self.metrics.detailed_feedback

        # Check if there's any actual feedback content
        has_content = any([
            feedback.commit_feedback,
            feedback.pr_title_feedback,
            feedback.review_tone_feedback,
            feedback.issue_feedback
        ])

        # If no feedback content exists, don't create the section
        if not has_content:
            return []

        lines = ["## 💡 코딩 습관 평가 및 스킬 향상 가이드", ""]
        lines.append("> 커밋 메시지, PR 제목, 리뷰 톤, 이슈 작성 등 코딩 습관을 분석하고 개선 방향을 제시합니다")
        lines.append("")

        # Commit message feedback
        if feedback.commit_feedback:
            lines.extend(self._build_commit_feedback(feedback.commit_feedback))

        # PR title feedback
        if feedback.pr_title_feedback:
            lines.extend(self._build_pr_title_feedback(feedback.pr_title_feedback))

        # Review tone feedback
        if feedback.review_tone_feedback:
            lines.extend(self._build_review_tone_feedback(feedback.review_tone_feedback))

        # Issue feedback
        if feedback.issue_feedback:
            lines.extend(self._build_issue_feedback(feedback.issue_feedback))

        lines.append("---")
        lines.append("")
        return lines

    def _build_feedback_table(
        self,
        title: str,
        feedback_data,
        good_category: str,
        poor_category: str,
        fallback_good_msg: str,
        fallback_poor_msg: str,
        evidence_formatter,
        link_formatter,
    ) -> List[str]:
        """Build a common feedback table format (HTML version).

        Args:
            title: Section title
            feedback_data: Feedback data object
            good_category: Category label for good examples
            poor_category: Category label for poor examples
            fallback_good_msg: Fallback message for non-dict good examples
            fallback_poor_msg: Fallback message for non-dict poor examples
            evidence_formatter: Function to format evidence from example dict
            link_formatter: Function to format link from example dict

        Returns:
            List of markdown lines
        """
        lines = [title, ""]

        # Build table rows
        headers = ["장점 혹은 개선점/보완점", "근거 (코드, 메세지 등)", "링크"]
        rows = []

        # Add good examples as strengths (장점)
        if hasattr(feedback_data, 'examples_good') and feedback_data.examples_good:
            for example in feedback_data.examples_good[:DISPLAY_LIMITS['feedback_examples']]:
                if isinstance(example, dict):
                    category = f"<strong>장점</strong>: {good_category}"
                    evidence = evidence_formatter(example)
                    link = link_formatter(example)
                    rows.append([category, evidence, link])
                else:
                    example_escaped = _escape_table_cell(str(example))
                    rows.append([f"<strong>장점</strong>: {fallback_good_msg}", example_escaped, "-"])

        # Add poor examples as improvement areas (개선점)
        if hasattr(feedback_data, 'examples_poor') and feedback_data.examples_poor:
            for example in feedback_data.examples_poor[:DISPLAY_LIMITS['feedback_examples']]:
                if isinstance(example, dict):
                    category = f"<strong>개선점</strong>: {poor_category}"
                    evidence = evidence_formatter(example)
                    link = link_formatter(example)
                    rows.append([category, evidence, link])
                else:
                    example_escaped = _escape_table_cell(str(example))
                    rows.append([f"<strong>개선점</strong>: {fallback_poor_msg}", example_escaped, "-"])

        # Handle improve examples (for review tone feedback)
        if hasattr(feedback_data, 'examples_improve') and feedback_data.examples_improve:
            for example in feedback_data.examples_improve[:DISPLAY_LIMITS['feedback_examples']]:
                if isinstance(example, dict):
                    category = f"<strong>개선점</strong>: {poor_category}"
                    evidence = evidence_formatter(example)
                    link = link_formatter(example)
                    rows.append([category, evidence, link])
                else:
                    example_escaped = _escape_table_cell(str(example))
                    rows.append([f"<strong>개선점</strong>: {fallback_poor_msg}", example_escaped, "-"])

        # Add suggestions as additional improvement areas
        if hasattr(feedback_data, 'suggestions') and feedback_data.suggestions:
            for suggestion in feedback_data.suggestions[:3]:  # Limit to 3 suggestions
                suggestion_escaped = _escape_table_cell(suggestion)
                rows.append([f"<strong>보완점</strong>: {suggestion_escaped}", "전반적인 패턴 분석 결과", "-"])

        # Render as HTML table
        lines.extend(GameRenderer.render_html_table(
            headers=headers,
            rows=rows,
            title="",
            description="",
            striped=True,
            escape_cells=False
        ))

        return lines

    def _build_commit_feedback(self, commit_feedback) -> List[str]:
        """Build commit feedback subsection with new table format."""
        def format_commit_evidence(example):
            message = example.get('message', '')
            reason = example.get('reason', '')
            suggestion = example.get('suggestion', '')

            # Escape special characters to prevent table breakage
            message_escaped = _escape_table_cell(message)
            reason_escaped = _escape_table_cell(reason)
            suggestion_escaped = _escape_table_cell(suggestion)

            # Build detailed evidence with message, reason, and suggestion
            parts = [f"**메시지**: `{message_escaped}`"]
            if reason_escaped:
                parts.append(f"<br>**근거**: {reason_escaped}")
            if suggestion_escaped:
                parts.append(f"<br>**개선방안**: {suggestion_escaped}")

            return "<br>".join(parts)

        def format_commit_link(example):
            if example.get('url'):
                sha_short = example.get('sha', '')[:7]
                url = _escape_table_cell(example.get('url', ''))
                return f"[{sha_short}]({url})"
            return example.get('sha', '')[:7]

        return self._build_feedback_table(
            title="### 📝 커밋 메시지 품질",
            feedback_data=commit_feedback,
            good_category="명확하고 의미있는 커밋 메시지",
            poor_category="커밋 메시지 구체화 필요",
            fallback_good_msg="좋은 커밋 메시지",
            fallback_poor_msg="커밋 메시지 개선 필요",
            evidence_formatter=format_commit_evidence,
            link_formatter=format_commit_link,
        )

    def _build_pr_title_feedback(self, pr_title_feedback) -> List[str]:
        """Build PR title feedback subsection with new table format."""
        def format_pr_evidence(example):
            title = example.get('title', '')
            reason = example.get('reason', '')
            suggestion = example.get('suggestion', '')

            # Escape special characters to prevent table breakage
            title_escaped = _escape_table_cell(title)
            reason_escaped = _escape_table_cell(reason)
            suggestion_escaped = _escape_table_cell(suggestion)

            # Build detailed evidence with title and reason
            parts = [f"**제목**: `{title_escaped}`"]
            if reason_escaped:
                parts.append(f"<br>**근거**: {reason_escaped}")
            if suggestion_escaped:
                parts.append(f"<br>**개선방안**: {suggestion_escaped}")

            return "<br>".join(parts)

        def format_pr_link(example):
            url = example.get('url', '')
            number = example.get('number', '')

            if url:
                url_escaped = _escape_table_cell(url)
                return f"[#{number}]({url_escaped})" if number else f"[PR]({url_escaped})"
            elif number:
                # Fallback: construct URL if not provided
                repo = self.metrics.repo or ""
                return f"[#{number}]({self.web_url}/{repo}/pull/{number})"
            return "-"

        return self._build_feedback_table(
            title="### 🔀 PR 제목 품질",
            feedback_data=pr_title_feedback,
            good_category="명확하고 구체적인 PR 제목",
            poor_category="PR 제목 구체화 필요",
            fallback_good_msg="좋은 PR 제목",
            fallback_poor_msg="PR 제목 개선 필요",
            evidence_formatter=format_pr_evidence,
            link_formatter=format_pr_link,
        )

    def _build_review_tone_feedback(self, review_tone_feedback) -> List[str]:
        """Build review tone feedback subsection with new table format."""
        def format_review_evidence(example):
            # Get the comment/body
            comment = example.get('comment', example.get('body', ''))
            strengths = example.get('strengths', [])
            issues = example.get('issues', [])
            improved_version = example.get('improved_version', '')

            # Escape special characters
            comment_escaped = _escape_table_cell(comment[:150] + "..." if len(comment) > 150 else comment)

            # Build detailed evidence
            parts = [f"**리뷰 코멘트**: `{comment_escaped}`"]

            # Add strengths for good examples
            if strengths:
                strengths_text = "<br>".join(f"• {_escape_table_cell(s)}" for s in strengths[:3])
                parts.append(f"<br>**장점**: <br>{strengths_text}")

            # Add issues for examples that need improvement
            if issues:
                issues_text = "<br>".join(f"• {_escape_table_cell(i)}" for i in issues[:3])
                parts.append(f"<br>**문제점**: <br>{issues_text}")

            # Add improved version if available
            if improved_version:
                improved_escaped = _escape_table_cell(improved_version[:150] + "..." if len(improved_version) > 150 else improved_version)
                parts.append(f"<br>**개선 예시**: `{improved_escaped}`")

            return "<br>".join(parts)

        def format_review_link(example):
            url = example.get('url', '')
            pr_number = example.get('pr_number', '')

            if url:
                url_escaped = _escape_table_cell(url)
                return f"[PR #{pr_number}]({url_escaped})"
            elif pr_number:
                return f"PR #{pr_number}"
            return "-"

        return self._build_feedback_table(
            title="### 👀 리뷰 톤 분석",
            feedback_data=review_tone_feedback,
            good_category="건설적이고 도움이 되는 리뷰",
            poor_category="리뷰 톤 개선 필요",
            fallback_good_msg="좋은 리뷰 톤",
            fallback_poor_msg="리뷰 톤 개선 필요",
            evidence_formatter=format_review_evidence,
            link_formatter=format_review_link,
        )

    def _build_issue_feedback(self, issue_feedback) -> List[str]:
        """Build issue feedback subsection with new table format."""
        def format_issue_evidence(example):
            title = _escape_table_cell(example.get('title', ''))
            return f"#{example.get('number', '')}: `{title}`"

        def format_issue_link(example):
            if example.get('url'):
                url = _escape_table_cell(example.get('url', ''))
                return f"[이슈 보기]({url})"
            return "-"

        return self._build_feedback_table(
            title="### 🐛 이슈 품질",
            feedback_data=issue_feedback,
            good_category="명확하고 상세한 이슈 작성",
            poor_category="이슈 설명 보완 필요",
            fallback_good_msg="좋은 이슈 작성",
            fallback_poor_msg="이슈 설명 개선 필요",
            evidence_formatter=format_issue_evidence,
            link_formatter=format_issue_link,
        )
