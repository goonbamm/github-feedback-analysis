"""Heuristic-based analysis utilities for fallback when LLM is unavailable."""

from __future__ import annotations

import re
from typing import Any, Callable

from .constants import HEURISTIC_THRESHOLDS, TEXT_LIMITS, REGEX_PATTERNS


class HeuristicAnalyzer:
    """Base class for heuristic-based analysis with common scoring patterns."""

    @staticmethod
    def classify_by_score(
        score: int,
        threshold: int,
        examples_good: list,
        examples_poor: list,
        item: dict,
        good_reason: str,
        poor_reason: str,
        max_examples: int = 3
    ) -> tuple[bool, int, int]:
        """Classify item by score and update example lists.

        Args:
            score: Calculated score for the item
            threshold: Threshold for classification
            examples_good: List to append good examples
            examples_poor: List to append poor examples
            item: Item to classify
            good_reason: Reason for good classification
            poor_reason: Reason for poor classification
            max_examples: Maximum examples to collect

        Returns:
            Tuple of (is_good, good_count_delta, poor_count_delta)
        """
        is_good = score >= threshold

        if is_good:
            if len(examples_good) < max_examples:
                examples_good.append({**item, "reason": good_reason})
            return True, 1, 0
        else:
            if len(examples_poor) < max_examples:
                examples_poor.append({**item, "reason": poor_reason})
            return False, 0, 1

    @staticmethod
    def check_length_score(text: str, min_len: int, max_len: int) -> tuple[int, list[str]]:
        """Check text length and return score and issues.

        Args:
            text: Text to check
            min_len: Minimum acceptable length
            max_len: Maximum acceptable length

        Returns:
            Tuple of (score, issues_list)
        """
        issues = []
        length = len(text)

        if min_len <= length <= max_len:
            return 1, issues

        if length < min_len:
            issues.append("텍스트가 너무 짧습니다")
        else:
            issues.append("텍스트가 너무 깁니다")

        return 0, issues

    @staticmethod
    def check_patterns(text: str, patterns: list[str], flags: int = 0) -> bool:
        """Check if text matches any of the given regex patterns.

        Args:
            text: Text to check
            patterns: List of regex patterns
            flags: Regex flags (e.g., re.IGNORECASE)

        Returns:
            True if any pattern matches, False otherwise
        """
        return any(re.match(pattern, text, flags) for pattern in patterns)

    @staticmethod
    def search_patterns(text: str, patterns: list[str], flags: int = 0) -> bool:
        """Check if text contains any of the given regex patterns.

        Args:
            text: Text to check
            patterns: List of regex patterns
            flags: Regex flags (e.g., re.IGNORECASE)

        Returns:
            True if any pattern is found, False otherwise
        """
        return any(re.search(pattern, text, flags) for pattern in patterns)

    @staticmethod
    def analyze_with_scoring(
        items: list[dict],
        score_fn: Callable[[dict], tuple[int, Any]],
        threshold: int,
        good_example_fn: Callable[[dict, Any], dict],
        poor_example_fn: Callable[[dict, Any], dict],
        max_examples: int = 3
    ) -> tuple[int, int, list[dict], list[dict]]:
        """Generic analysis using a scoring function.

        Args:
            items: List of items to analyze
            score_fn: Function that scores an item and returns (score, metadata)
            threshold: Score threshold for good classification
            good_example_fn: Function to format good examples
            poor_example_fn: Function to format poor examples
            max_examples: Maximum examples to collect

        Returns:
            Tuple of (good_count, poor_count, examples_good, examples_poor)
        """
        good_count = 0
        poor_count = 0
        examples_good = []
        examples_poor = []

        for item in items:
            score, metadata = score_fn(item)

            if score >= threshold:
                good_count += 1
                if len(examples_good) < max_examples:
                    examples_good.append(good_example_fn(item, metadata))
            else:
                poor_count += 1
                if len(examples_poor) < max_examples:
                    examples_poor.append(poor_example_fn(item, metadata))

        return good_count, poor_count, examples_good, examples_poor


class CommitMessageAnalyzer:
    """Heuristic analyzer for commit messages."""

    @staticmethod
    def score_commit_message(
        first_line: str,
        lines: list[str],
        good_patterns: list[str],
        poor_patterns: list[str],
        min_len: int,
        max_len: int,
        too_long: int,
        min_body_len: int
    ) -> tuple[int, list[str]]:
        """Score a commit message and return score with issues list.

        Args:
            first_line: First line of commit message
            lines: All lines of commit message
            good_patterns: Regex patterns for good messages
            poor_patterns: Regex patterns for poor messages
            min_len: Minimum length threshold
            max_len: Maximum length threshold
            too_long: Too long threshold
            min_body_len: Minimum body length

        Returns:
            Tuple of (score, issues_list)
        """
        score = 0
        issues = []

        # Check length
        if min_len <= len(first_line) <= max_len:
            score += 1
        elif len(first_line) < min_len:
            issues.append("메시지가 너무 짧습니다")
        elif len(first_line) > too_long:
            issues.append("첫 줄이 너무 깁니다")

        # Check for good patterns
        if HeuristicAnalyzer.check_patterns(first_line, good_patterns, re.IGNORECASE):
            score += 2

        # Check for poor patterns
        if HeuristicAnalyzer.check_patterns(first_line.lower(), poor_patterns):
            score -= 2
            issues.append("모호하거나 임시 메시지입니다")

        # Check for body
        if len(lines) > 2 and len(lines[2].strip()) > min_body_len:
            score += 1

        return score, issues

    @staticmethod
    def analyze(commits: list[dict[str, str]]) -> dict[str, Any]:
        """Enhanced heuristic-based commit message analysis.

        Args:
            commits: List of commit dictionaries with 'sha' and 'message' keys

        Returns:
            Analysis results dictionary
        """
        # Patterns for classification
        good_patterns = [
            r'^(feat|fix|docs|style|refactor|test|chore|perf|ci|build|revert)(\(.+\))?: .+',
            r'^(Add|Fix|Update|Refactor|Remove|Implement|Improve|Optimize) [A-Z].+',
            r'^[A-Z][a-z]+ .+ (#\d+|issue|pr)',
        ]
        poor_patterns = [
            r'^(wip|tmp|test|debug|asdf|aaa|zzz)',
            r'^fix$|^update$|^bug$',
            r'^.{1,5}$',
            r'^.{150,}',
        ]

        # Thresholds
        min_len = HEURISTIC_THRESHOLDS['commit_min_length']
        max_len = HEURISTIC_THRESHOLDS['commit_max_length']
        too_long = HEURISTIC_THRESHOLDS['commit_too_long']
        min_body_len = HEURISTIC_THRESHOLDS['commit_min_body_length']
        good_score_threshold = HEURISTIC_THRESHOLDS['review_good_score']

        # Define scoring function
        def score_fn(commit):
            message = commit["message"].strip()
            lines = message.split("\n")
            first_line = lines[0] if lines else ""
            score, issues = CommitMessageAnalyzer.score_commit_message(
                first_line, lines, good_patterns, poor_patterns,
                min_len, max_len, too_long, min_body_len
            )
            return score, (first_line, issues)

        # Define example formatters
        def good_example_fn(commit, metadata):
            first_line, _ = metadata
            reasons = []
            reasons.append(f"적절한 길이({len(first_line)}자)로 가독성이 좋습니다.")
            if REGEX_PATTERNS['conventional_commit'].match(first_line):
                reasons.append("Conventional Commits 형식을 따라 타입이 명확합니다.")
            if REGEX_PATTERNS['imperative_commit'].match(first_line):
                reasons.append("명령형 동사로 시작하여 일관된 스타일을 유지합니다.")
            if '#' in first_line or 'issue' in first_line.lower() or 'pr' in first_line.lower():
                reasons.append("Issue/PR 참조를 포함하여 맥락을 제공합니다.")

            reason = " ".join(reasons) if reasons else "적절한 형식의 커밋 메시지입니다."

            return {
                "message": first_line,
                "sha": commit["sha"],
                "reason": reason
            }

        def poor_example_fn(commit, metadata):
            first_line, issues = metadata
            reason_parts = []
            if "너무 짧습니다" in ", ".join(issues):
                reason_parts.append(f"메시지가 너무 짧아({len(first_line)}자) 변경 내용을 충분히 설명하지 못합니다.")
            if "너무 깁니다" in ", ".join(issues):
                reason_parts.append(f"첫 줄이 너무 길어({len(first_line)}자) 가독성이 떨어집니다. 50-72자 이내로 작성하는 것이 좋습니다.")
            if "모호하거나 임시 메시지입니다" in ", ".join(issues):
                reason_parts.append("'wip', 'fix', 'tmp' 같은 모호한 단어만 사용하여 변경 의도를 알 수 없습니다.")

            if not reason_parts and issues:
                reason_parts.append(", ".join(issues))

            reason = " ".join(reason_parts) if reason_parts else "커밋 메시지 작성 규칙을 따르지 않아 개선이 필요합니다."

            suggestions = []
            if len(first_line) < min_len:
                suggestions.append(f"메시지를 더 구체적으로 작성하세요 (예: 'feat: 사용자 인증 기능 추가')")
            elif len(first_line) > max_len:
                suggestions.append("첫 줄을 간결하게 요약하고, 자세한 내용은 본문에 작성하세요")
            else:
                suggestions.append("Conventional Commits 형식을 사용하세요 (예: feat(auth): 로그인 기능 구현)")

            return {
                "message": first_line,
                "sha": commit["sha"],
                "reason": reason,
                "suggestion": " ".join(suggestions)
            }

        # Use generic analyzer
        good_count, poor_count, examples_good, examples_poor = HeuristicAnalyzer.analyze_with_scoring(
            commits, score_fn, good_score_threshold, good_example_fn, poor_example_fn,
            max_examples=TEXT_LIMITS['example_display_limit']
        )

        return {
            "good_messages": good_count,
            "poor_messages": poor_count,
            "suggestions": [
                "커밋 메시지의 첫 줄은 50-72자 이내로 작성하세요.",
                "Conventional Commits 형식을 사용하세요: type(scope): subject",
                "명령형 동사로 시작하세요 (Add, Fix, Update, Refactor 등).",
                "본문에 변경 이유를 상세히 설명하세요 (무엇보다 왜가 중요).",
                "이슈나 PR 번호를 참조하세요 (#123, closes #456 등).",
            ],
            "examples_good": examples_good,
            "examples_poor": examples_poor,
        }


class PRTitleAnalyzer:
    """Heuristic analyzer for PR titles."""

    @staticmethod
    def score_pr_title(
        title: str,
        clear_patterns: list[str],
        vague_keywords: set[str],
        min_len: int,
        max_len: int,
        min_words: int
    ) -> tuple[int, list[str]]:
        """Score a PR title and return score with reasons list.

        Args:
            title: PR title to score
            clear_patterns: Regex patterns for clear titles
            vague_keywords: Set of vague keywords
            min_len: Minimum length
            max_len: Maximum length
            min_words: Minimum word count

        Returns:
            Tuple of (score, reasons_list)
        """
        score = 0
        reasons = []

        # Check length
        if min_len <= len(title) <= max_len:
            score += 1
        elif len(title) < min_len:
            reasons.append("제목이 너무 짧습니다")
        else:
            reasons.append("제목이 너무 깁니다")

        # Check for clear patterns
        has_clear_pattern = HeuristicAnalyzer.check_patterns(title, clear_patterns, re.IGNORECASE)
        if has_clear_pattern:
            score += 2

        # Check for vague keywords
        first_word = title.split()[0].lower() if title.split() else ""
        if first_word in vague_keywords and not has_clear_pattern:
            score -= 1
            reasons.append("너무 일반적인 단어로 시작합니다")

        # Check for specificity
        if len(title.split()) >= min_words:
            score += 1

        return score, reasons

    @staticmethod
    def analyze(prs: list[dict[str, str]]) -> dict[str, Any]:
        """Enhanced heuristic-based PR title analysis.

        Args:
            prs: List of PR dictionaries with 'number' and 'title' keys

        Returns:
            Analysis results dictionary
        """
        # Patterns and configuration
        clear_patterns = [
            r'^\[(feat|fix|docs|style|refactor|test|chore|perf|ci|build)\].+',
            r'^(feat|fix|docs|style|refactor|test|chore|perf|ci|build):.+',
            r'^(Add|Fix|Update|Refactor|Remove|Implement|Improve) .+',
        ]
        vague_keywords = {'update', 'fix', 'change', 'modify', 'edit', 'misc', 'various', 'stuff', 'things', 'code', 'work'}

        min_len = HEURISTIC_THRESHOLDS['pr_title_min_length']
        max_len = HEURISTIC_THRESHOLDS['pr_title_max_length']
        min_words = HEURISTIC_THRESHOLDS['pr_title_min_words']
        good_score = HEURISTIC_THRESHOLDS['review_good_score']

        # Define scoring function
        def score_fn(pr):
            title = pr["title"].strip()
            score, reasons = PRTitleAnalyzer.score_pr_title(
                title, clear_patterns, vague_keywords, min_len, max_len, min_words
            )
            return score, (title, reasons)

        # Define example formatters
        def good_example_fn(pr, metadata):
            title, _ = metadata
            return {
                "number": pr["number"],
                "title": title,
                "reason": "명확하고 설명적인 제목입니다",
                "score": min(10, score_fn(pr)[0] * 3)
            }

        def poor_example_fn(pr, metadata):
            title, reasons = metadata
            first_word = title.split()[0].lower() if title.split() else "feat"
            suggestion_type = first_word if first_word in {'feat', 'fix', 'docs'} else 'feat'
            return {
                "number": pr["number"],
                "title": title,
                "reason": ", ".join(reasons) if reasons else "제목이 모호합니다",
                "suggestion": f"[{suggestion_type}] {title if len(title) > 10 else title + ' - 구체적인 변경 내용 설명'}"
            }

        # Use generic analyzer
        clear_count, vague_count, examples_good, examples_poor = HeuristicAnalyzer.analyze_with_scoring(
            prs, score_fn, good_score, good_example_fn, poor_example_fn,
            max_examples=3
        )

        return {
            "clear_titles": clear_count,
            "vague_titles": vague_count,
            "suggestions": [
                "PR 제목은 15-80자 사이로 작성하세요.",
                "타입을 명시하세요: [feat], [fix], [docs], [refactor] 등.",
                "'update', 'fix' 같은 일반적 단어만 사용하지 말고 구체적으로 설명하세요.",
                "명령형 동사로 시작하세요: Add, Fix, Implement, Refactor 등.",
                "변경의 범위와 영향을 제목에 포함하세요.",
            ],
            "examples_good": examples_good,
            "examples_poor": examples_poor,
        }


class ReviewToneAnalyzer:
    """Heuristic analyzer for review tone."""

    @staticmethod
    def analyze(reviews: list[dict[str, str]]) -> dict[str, Any]:
        """Enhanced heuristic-based review tone analysis.

        Args:
            reviews: List of review dictionaries with 'body' key

        Returns:
            Analysis results dictionary
        """
        # Patterns for classification
        constructive_patterns = [
            r'어떨까요|고려해|제안|추천|생각해보',
            r'같아요|것 같|보입니다',
            r'해보면|시도해|시험해',
            r'\?',
            r'좋을 것|나을 것|더 좋',
            r'예시|예를 들어|이렇게|다음과 같이',
            r'👍|✅|💯|🎉|😊|👏',
        ]

        harsh_patterns = [
            r'잘못|틀렸|오류|에러(?!:)|문제(?!를 해결)',
            r'다시|반드시|꼭|절대|필수',
            r'왜|이유(?! 없)',
            r'(?<!더 )나쁨|형편없|최악',
            r'이해(?! 가능|할 수)',
        ]

        positive_indicators = [
            r'좋|훌륭|멋|잘|감사|고마|수고',
            r'명확|깔끔|간결|효율|효과',
            r'LGTM|looks good|nice|great|excellent',
        ]

        constructive_count = 0
        harsh_count = 0
        neutral_count = 0
        examples_good = []
        examples_improve = []

        for review in reviews:
            body = review.get("body", "").strip()
            if not body:
                continue

            # Score the review
            score = 0
            strengths = []
            issues = []

            # Check for constructive patterns
            constructive_matches = sum(1 for p in constructive_patterns if re.search(p, body, re.IGNORECASE))
            if constructive_matches > 0:
                score += constructive_matches
                if REGEX_PATTERNS['suggestion_markers'].search(body):
                    strengths.append("제안형 표현을 사용하여 존중하는 톤을 유지합니다")
                if REGEX_PATTERNS['example_markers'].search(body):
                    strengths.append("구체적인 예시를 제공하여 이해를 돕습니다")
                if REGEX_PATTERNS['positive_emojis'].search(body):
                    strengths.append("이모지를 활용하여 긍정적인 분위기를 조성합니다")

            # Check for harsh patterns
            harsh_matches = sum(1 for p in harsh_patterns if re.search(p, body, re.IGNORECASE))
            if harsh_matches > 0:
                score -= harsh_matches * 2
                if REGEX_PATTERNS['harsh_words'].search(body):
                    issues.append("부정적인 직접 지적으로 상대방의 감정을 상하게 할 수 있습니다")
                if REGEX_PATTERNS['demanding_words'].search(body):
                    issues.append("명령형 표현으로 강압적으로 느껴질 수 있습니다")

            # Check for positive indicators
            positive_matches = sum(1 for p in positive_indicators if re.search(p, body, re.IGNORECASE))
            if positive_matches > 0:
                score += positive_matches
                if REGEX_PATTERNS['positive_words'].search(body):
                    strengths.append("긍정적인 피드백을 포함하여 동기를 부여합니다")

            # Classify based on score
            if score >= 2:
                constructive_count += 1
                if len(examples_good) < 3 and strengths:
                    examples_good.append({
                        "pr_number": review.get("pr_number", ""),
                        "author": review.get("author", ""),
                        "comment": body[:150] + "..." if len(body) > 150 else body,
                        "url": review.get("url", ""),
                        "strengths": strengths[:3],
                    })
            elif score <= -2:
                harsh_count += 1
                if len(examples_improve) < 3:
                    # Create improved version
                    improved = body
                    improved = REGEX_PATTERNS['harsh_words'].sub('개선이 필요한 부분', improved)
                    improved = re.sub(r'다시\s+(\w+)', r'\1하면 어떨까요', improved)  # Complex pattern, keep inline
                    improved = REGEX_PATTERNS['demanding_words'].sub('~하면 좋을 것 같습니다', improved)

                    examples_improve.append({
                        "pr_number": review.get("pr_number", ""),
                        "author": review.get("author", ""),
                        "comment": body[:150] + "..." if len(body) > 150 else body,
                        "url": review.get("url", ""),
                        "issues": issues[:3] if issues else ["더 부드러운 표현을 사용하면 좋겠습니다"],
                        "improved_version": improved[:200] + "..." if len(improved) > 200 else improved,
                    })
            else:
                neutral_count += 1

        # Generate suggestions
        suggestions = []
        if harsh_count > 0:
            suggestions.append("명령형 표현 대신 제안형 표현을 사용하세요 (예: '~하세요' → '~하면 어떨까요?')")
        if constructive_count < len(reviews) * 0.5:
            suggestions.append("구체적인 개선 방안과 예시를 함께 제공하세요")
        if len([r for r in reviews if REGEX_PATTERNS['positive_emojis'].search(r.get("body", ""))]) < len(reviews) * 0.3:
            suggestions.append("긍정적인 피드백과 함께 이모지를 활용하여 친근한 분위기를 만드세요")

        # Default suggestions if none generated
        if not suggestions:
            suggestions = [
                "리뷰 코멘트는 건설적이고 존중하는 톤을 유지하세요.",
                "구체적인 개선 제안을 포함하세요.",
                "긍정적인 피드백도 함께 제공하세요.",
            ]

        return {
            "constructive_reviews": constructive_count,
            "harsh_reviews": harsh_count,
            "neutral_reviews": neutral_count,
            "suggestions": suggestions,
            "examples_good": examples_good,
            "examples_improve": examples_improve,
        }


class IssueQualityAnalyzer:
    """Heuristic analyzer for issue quality."""

    @staticmethod
    def score_issue_quality(
        body: str,
        body_short: int,
        body_detailed: int,
        good_score: int
    ) -> tuple[int, list[str], list[str]]:
        """Score issue quality and return score, strengths, and missing elements.

        Args:
            body: Issue body text
            body_short: Short body threshold
            body_detailed: Detailed body threshold
            good_score: Good score threshold

        Returns:
            Tuple of (score, strengths, missing_elements)
        """
        score = 0
        strengths = []
        missing = []

        # Check body length
        if len(body) > body_detailed:
            score += 2
            strengths.append("상세한 설명")
        elif len(body) > body_short:
            score += 1
        else:
            missing.append("본문이 너무 짧습니다")

        # Check for structured information
        structured_checks = [
            (r'(steps to reproduce|재현 단계|how to reproduce)', "재현 단계 포함", "재현 단계", 2),
            (r'(expected|actual|예상|실제)', "예상/실제 결과 비교", "예상/실제 결과", 1),
            (r'(environment|version|os|browser|환경)', "환경 정보 포함", "환경 정보", 1),
            (r'(screenshot|image|!\\[|스크린샷)', "스크린샷/이미지 첨부", None, 1),
        ]

        for pattern, strength, missing_name, points in structured_checks:
            if re.search(pattern, body, re.IGNORECASE):
                score += points
                strengths.append(strength)
            elif missing_name and score < good_score - 1:
                missing.append(missing_name)

        # Check for code blocks
        if '```' in body or '`' in body:
            score += 1
            strengths.append("코드 예시 포함")

        # Check for links/references
        if REGEX_PATTERNS['issue_reference'].search(body):
            score += 1

        return score, strengths, missing

    @staticmethod
    def detect_issue_type(title: str, body: str) -> str:
        """Detect issue type from title and body.

        Args:
            title: Issue title
            body: Issue body

        Returns:
            Issue type: 'bug', 'feature', 'question', or 'other'
        """
        text = (title + " " + body).lower()

        if REGEX_PATTERNS['bug_keywords'].search(text):
            return "bug"
        elif REGEX_PATTERNS['feature_keywords'].search(text):
            return "feature"
        elif REGEX_PATTERNS['question_keywords'].search(text):
            return "question"
        else:
            return "other"

    @staticmethod
    def analyze(issues: list[dict[str, str]]) -> dict[str, Any]:
        """Enhanced heuristic-based issue quality analysis.

        Args:
            issues: List of issue dictionaries with 'number', 'title', 'body' keys

        Returns:
            Analysis results dictionary
        """
        body_short = HEURISTIC_THRESHOLDS['issue_body_short']
        body_detailed = HEURISTIC_THRESHOLDS['issue_body_detailed']
        good_score = HEURISTIC_THRESHOLDS['issue_good_score']

        # Define scoring function
        def score_fn(issue):
            body = issue.get("body", "").strip()
            title = issue.get("title", "").strip()
            score, strengths, missing = IssueQualityAnalyzer.score_issue_quality(
                body, body_short, body_detailed, good_score
            )
            return score, (title, body, strengths, missing)

        # Define example formatters
        def good_example_fn(issue, metadata):
            title, body, strengths, _ = metadata
            return {
                "number": issue["number"],
                "title": title,
                "type": IssueQualityAnalyzer.detect_issue_type(title, body),
                "strengths": strengths[:3],
                "completeness_score": min(10, score_fn(issue)[0])
            }

        def poor_example_fn(issue, metadata):
            title, _, _, missing = metadata
            return {
                "number": issue["number"],
                "title": title,
                "missing_elements": missing,
                "suggestion": "이슈 템플릿을 사용하거나 재현 단계, 예상/실제 결과, 환경 정보를 추가하세요."
            }

        # Use generic analyzer
        well_described, poorly_described, examples_good, examples_poor = HeuristicAnalyzer.analyze_with_scoring(
            issues, score_fn, good_score, good_example_fn, poor_example_fn,
            max_examples=3
        )

        return {
            "well_described": well_described,
            "poorly_described": poorly_described,
            "suggestions": [
                "이슈 본문에 상세한 설명을 포함하세요 (최소 100자 이상).",
                "Bug Report: 재현 단계, 예상 결과, 실제 결과, 환경 정보를 포함하세요.",
                "Feature Request: 해결하려는 문제, 제안하는 솔루션, 사용 시나리오를 설명하세요.",
                "코드 블록(```)이나 스크린샷을 활용하여 시각적으로 설명하세요.",
                "관련 이슈나 PR을 참조하세요 (#123 형식).",
            ],
            "examples_good": examples_good,
            "examples_poor": examples_poor,
        }
