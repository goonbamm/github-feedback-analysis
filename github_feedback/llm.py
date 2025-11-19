"""Utility helpers for interacting with Large Language Model endpoints."""

from __future__ import annotations

import json
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from itertools import islice
from typing import Any

import requests

from .console import Console
from .constants import HEURISTIC_THRESHOLDS, LLM_DEFAULTS, TEXT_LIMITS, THREAD_POOL_CONFIG
from .hybrid_analysis import HybridAnalyzer
from .llm_cache import (
    DEFAULT_CACHE_EXPIRE_DAYS,
    get_cache_key,
    load_from_cache,
    save_to_cache,
)
from .llm_heuristics import (
    CommitMessageAnalyzer,
    IssueQualityAnalyzer,
    PRTitleAnalyzer,
    ReviewToneAnalyzer,
)
from .llm_metrics import LLMCallMetrics, get_global_collector
from .llm_validation import LLMResponseValidator
from .models import PullRequestReviewBundle, ReviewPoint, ReviewSummary
from .prompts import (
    get_award_summary_quote_system_prompt,
    get_award_summary_quote_user_prompt,
    get_commit_analysis_system_prompt,
    get_commit_analysis_user_prompt,
    get_issue_quality_analysis_system_prompt,
    get_issue_quality_analysis_user_prompt,
    get_pr_review_system_prompt,
    get_pr_title_analysis_system_prompt,
    get_pr_title_analysis_user_prompt,
    get_review_tone_analysis_system_prompt,
    get_review_tone_analysis_user_prompt,
)
from .utils import limit_items, truncate_patch

logger = logging.getLogger(__name__)
console = Console()


# Default values (used when config is not available)
MAX_PATCH_LINES_PER_FILE = LLM_DEFAULTS['max_patch_lines_per_file']
MAX_FILES_WITH_PATCH_SNIPPETS = LLM_DEFAULTS['max_files_with_patch_snippets']

# HTTP Status codes for retry logic
RETRYABLE_STATUS_CODES = frozenset({429, 408, 500, 502, 503, 504})  # Rate limit, timeout, server errors
PERMANENT_ERROR_STATUS_CODES = frozenset({400, 401, 403, 404, 422})  # Bad request, auth, not found


@dataclass(frozen=True, slots=True)
class AnalysisConfig:
    """Configuration for LLM analysis tasks."""

    analysis_type: str  # e.g., "commit messages", "PR titles"
    sample_size: int
    system_prompt: str
    user_prompt_template: str  # Format string with {data_list} placeholder
    empty_result: dict[str, Any]
    fallback_method_name: str


def _format_analysis_data(data: list[dict[str, str]], analysis_type: str) -> str:
    """Format data items for LLM analysis prompts.

    Args:
        data: List of data items to format
        analysis_type: Type of analysis (e.g., "commits", "prs", "reviews", "issues")

    Returns:
        Formatted string ready for LLM prompt
    """
    if analysis_type == "commits":
        return "\n".join([
            f"{i+1}. {data[i]['message'][:TEXT_LIMITS['commit_message_display_length']]} (SHA: {data[i]['sha'][:7]})"
            for i in range(len(data))
        ])
    elif analysis_type == "prs":
        return "\n".join([
            f"{i+1}. #{data[i]['number']}: {data[i]['title']}"
            for i in range(len(data))
        ])
    elif analysis_type == "reviews":
        return "\n".join([
            f"{i+1}. (PR #{data[i]['pr_number']}, {data[i]['author']}): {data[i]['body'][:200]}"
            for i in range(len(data))
        ])
    elif analysis_type == "issues":
        return "\n".join([
            f"{i+1}. #{data[i]['number']}: {data[i]['title']}\n   본문: {data[i].get('body', '')[:150]}"
            for i in range(len(data))
        ])
    else:
        # Fallback: just stringify items
        return "\n".join([f"{i+1}. {item}" for i, item in enumerate(data)])


@dataclass(slots=True)
class LLMClient:
    """Minimal HTTP client for chat-completion style LLM APIs."""

    endpoint: str
    model: str = ""
    timeout: int = 60
    max_files_in_prompt: int = 10
    max_files_with_patch_snippets: int = 5
    enable_cache: bool = True
    cache_expire_days: int = DEFAULT_CACHE_EXPIRE_DAYS
    rate_limit_delay: float = 0.0  # Delay between requests in seconds (0 = no limit)
    web_url: str = "https://github.com"  # GitHub web URL for generating links

    def _build_messages(self, bundle: PullRequestReviewBundle) -> list[dict[str, str]]:
        """Create the prompt messages describing the pull request."""

        summary_lines = [
            f"저장소: {bundle.repo}",
            f"Pull Request: #{bundle.number} {bundle.title}",
            f"작성자: {bundle.author or 'unknown'}",
            f"변경 통계: +{bundle.additions} / -{bundle.deletions} ({bundle.changed_files}개 파일)",
            "",
            "Pull Request 본문:",
            bundle.body or "<비어있음>",
            "",
        ]

        if bundle.review_bodies:
            summary_lines.append("기존 리뷰:")
            summary_lines.extend(f"- {body}" for body in bundle.review_bodies)
            summary_lines.append("")

        if bundle.review_comments:
            summary_lines.append("인라인 리뷰 코멘트:")
            summary_lines.extend(f"- {comment}" for comment in bundle.review_comments[:LLM_DEFAULTS['sample_size_commits']])
            summary_lines.append("")

        summary_lines.append("변경된 파일:")
        for index, file in enumerate(limit_items(bundle.files, self.max_files_in_prompt)):
            summary_lines.append(
                f"- {file.filename} ({file.status}, +{file.additions}/-{file.deletions}, 변경={file.changes})"
            )
            if (
                index < self.max_files_with_patch_snippets
                and file.patch
                and (snippet := truncate_patch(file.patch, MAX_PATCH_LINES_PER_FILE))
            ):
                summary_lines.append("```diff")
                summary_lines.append(snippet)
                summary_lines.append("```")
        summary_lines.append("")

        prompt = "\n".join(summary_lines)

        return [
            {
                "role": "system",
                "content": get_pr_review_system_prompt(),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ]

    def _analyze_with_config(
        self,
        data: list[dict[str, str]],
        config: AnalysisConfig,
        data_formatter_type: str,
    ) -> dict[str, Any]:
        """Generic analysis method using configuration.

        This template method reduces duplication across analysis methods by
        centralizing the common pattern: validation, sampling, LLM call,
        error handling, and fallback.

        Args:
            data: Input data to analyze
            config: Analysis configuration
            data_formatter_type: Type hint for data formatting ("commits", "prs", etc.)

        Returns:
            Analysis results dictionary
        """
        # Return empty result if no data
        if not data:
            return config.empty_result

        # Sample data
        sample_data = list(islice(data, config.sample_size))

        try:
            # Format data for prompt
            data_list = _format_analysis_data(sample_data, data_formatter_type)

            # Build messages
            messages = [
                {
                    "role": "system",
                    "content": config.system_prompt,
                },
                {
                    "role": "user",
                    "content": config.user_prompt_template.format(data_list=data_list),
                },
            ]

            # Call LLM
            response = self.complete(messages)

            # Check for empty response
            if not response or not response.strip():
                raise ValueError("Empty response from LLM")

            result = json.loads(response)

            return result

        except (ValueError, requests.RequestException, json.JSONDecodeError) as exc:
            # Fallback to heuristics
            logger.warning(f"LLM {config.analysis_type} analysis failed: {exc}")
            console.print(
                f"[warning]⚠ LLM {config.analysis_type} analysis unavailable - using heuristic analysis[/]",
                style="warning",
            )
            fallback_method = getattr(self, config.fallback_method_name)
            return fallback_method(sample_data)

    def _parse_points(self, payload: list[Any] | tuple[Any, ...]) -> list[ReviewPoint]:
        """Normalise payload entries into :class:`ReviewPoint` objects."""

        points: List[ReviewPoint] = []
        for item in payload:
            if isinstance(item, dict):
                message = str(item.get("message") or item.get("summary") or "").strip()
                example_raw = item.get("example") or item.get("detail")
                example = str(example_raw).strip() if example_raw else None
            else:
                message = str(item).strip()
                example = None
            if message:
                points.append(ReviewPoint(message=message, example=example or None))
        return points

    def _parse_response(self, response_payload: Dict[str, Any]) -> ReviewSummary:
        """Extract the JSON content from the LLM response."""

        choices = response_payload.get("choices")
        if not choices:
            raise ValueError("LLM response missing 'choices' array")

        if not isinstance(choices, list) or len(choices) == 0:
            raise ValueError("LLM response 'choices' array is empty")

        message = choices[0].get("message")
        if not message:
            raise ValueError("LLM response missing 'message' object")

        content = message.get("content", "").strip()
        if not content:
            raise ValueError("LLM response message has empty content")

        try:
            raw = json.loads(content)
        except json.JSONDecodeError as exc:  # pragma: no cover - defensive fallback
            raise ValueError(f"LLM response was not valid JSON: {exc}") from exc

        # Validate required fields in parsed JSON
        if not isinstance(raw, dict):
            raise ValueError("LLM response JSON must be an object")

        if "overview" not in raw:
            raise ValueError("LLM response missing required 'overview' field")

        overview = str(raw.get("overview", "")).strip()
        if not overview:
            raise ValueError("LLM response 'overview' field cannot be empty")

        strengths = self._parse_points(raw.get("strengths", []))
        improvements = self._parse_points(raw.get("improvements", []))

        return ReviewSummary(overview=overview, strengths=strengths, improvements=improvements)

    @staticmethod
    def _is_json_format_error(exc: requests.HTTPError) -> bool:
        """Check if an HTTP error is related to JSON format issues that can be retried.

        Args:
            exc: The HTTP error exception to check.

        Returns:
            True if this is a retryable JSON format error, False otherwise.
        """
        if exc.response is None:
            return False

        status_code = exc.response.status_code

        # Server errors (5xx) are always retryable
        if status_code >= 500:
            return True

        # For client errors, check if they're related to JSON format
        if status_code in {400, 404, 415, 422}:
            try:
                error_text_lower = exc.response.text.lower()
                return "json_object" in error_text_lower or "response_format" in error_text_lower
            except (AttributeError, UnicodeDecodeError, LookupError):  # pragma: no cover - defensive guard
                return False

        return False

    def generate_review(self, bundle: PullRequestReviewBundle) -> ReviewSummary:
        """Invoke the configured LLM endpoint and parse the structured feedback."""

        base_payload = {
            "model": self.model or "default-model",
            "messages": self._build_messages(bundle),
            "temperature": HEURISTIC_THRESHOLDS['llm_temperature'],
        }

        request_payloads: List[Dict[str, Any]] = [
            base_payload | {"response_format": {"type": "json_object"}}
        ]
        request_payloads.append(base_payload)

        last_error: Optional[Exception] = None
        for request_payload in request_payloads:
            try:
                response = requests.post(
                    self.endpoint,
                    json=request_payload,
                    timeout=self.timeout,
                )
                response.raise_for_status()

                # Check for empty response
                if not response.content or not response.content.strip():
                    last_error = ValueError("Empty response from LLM endpoint")
                    if "response_format" in request_payload:
                        continue
                    raise last_error

                try:
                    response_payload = response.json()
                except ValueError as exc:  # pragma: no cover - upstream bug/HTML error page
                    last_error = ValueError("LLM response was not valid JSON")
                    if "response_format" in request_payload:
                        continue
                    raise last_error from exc

                try:
                    return self._parse_response(response_payload)
                except ValueError as exc:
                    last_error = exc
                    if "response_format" in request_payload:
                        continue
                    raise
            except requests.HTTPError as exc:
                last_error = exc

                # If using response_format and it's a retryable JSON format error, try again without it
                if "response_format" in request_payload and self._is_json_format_error(exc):
                    continue

                raise
            except (OSError, ConnectionError, TimeoutError) as exc:  # pragma: no cover - network failures already handled elsewhere
                last_error = exc
                break

        if last_error is not None:
            raise last_error

        raise RuntimeError("LLM request failed without raising an explicit error")

    def test_connection(self) -> None:
        """Test connection to the LLM endpoint with a simple request.

        Raises:
            requests.RequestException: If connection fails
            ValueError: If response format is invalid
        """
        test_messages = [
            {
                "role": "system",
                "content": "You are a helpful assistant.",
            },
            {
                "role": "user",
                "content": "Hello",
            },
        ]

        payload = {
            "model": self.model or "default-model",
            "messages": test_messages,
            "temperature": HEURISTIC_THRESHOLDS['llm_temperature'],
            "max_tokens": HEURISTIC_THRESHOLDS['llm_test_max_tokens'],
        }

        # Use shorter timeout for test connection
        test_timeout = THREAD_POOL_CONFIG['test_connection_timeout']
        response = requests.post(
            self.endpoint,
            json=payload,
            timeout=min(self.timeout, test_timeout),
        )
        response.raise_for_status()

        # Check for empty response
        if not response.content or not response.content.strip():
            raise ValueError("Empty response from LLM endpoint")

        try:
            response_payload = response.json()
        except ValueError as exc:
            raise ValueError("LLM endpoint returned invalid JSON") from exc

        choices = response_payload.get("choices")
        if not choices:
            raise ValueError("LLM endpoint response format is invalid (missing 'choices')")

    def _check_cache(
        self,
        messages: list[dict[str, str]],
        temperature: float,
    ) -> tuple[str | None, str | None]:
        """Check cache for existing response.

        Args:
            messages: Chat messages for the LLM
            temperature: Sampling temperature

        Returns:
            Tuple of (cached_response, cache_key) where cached_response is None if not found
        """
        if not self.enable_cache:
            return None, None

        cache_data = {
            "messages": messages,
            "temperature": temperature,
            "model": self.model,
        }
        cache_key = get_cache_key(cache_data)
        cached_response = load_from_cache(cache_key, self.cache_expire_days)

        return cached_response, cache_key

    def _validate_response(self, response: requests.Response) -> str:
        """Validate and extract content from LLM response.

        Args:
            response: HTTP response from LLM endpoint

        Returns:
            Extracted content string

        Raises:
            ValueError: If response format is invalid or content is missing
        """
        # Check for empty response
        if not response.content or not response.content.strip():
            raise ValueError("Empty response from LLM endpoint")

        try:
            response_payload = response.json()
        except ValueError as exc:  # pragma: no cover - upstream bug/HTML error page
            raise ValueError("LLM response was not valid JSON") from exc

        choices = response_payload.get("choices") or []
        if not choices:
            raise ValueError("LLM response did not contain choices")

        message = choices[0].get("message") or {}
        content = str(message.get("content") or "").strip()
        if not content:
            raise ValueError("LLM response did not contain content")

        return content

    def _should_retry_error(self, exc: Exception) -> bool:
        """Determine if an error should trigger a retry.

        Args:
            exc: Exception that occurred during request

        Returns:
            True if error is retryable, False if it's permanent

        Raises:
            Exception: Re-raises the exception if it's non-retryable
        """
        if isinstance(exc, requests.HTTPError):
            status_code = exc.response.status_code
            # Don't retry on permanent client errors
            if status_code in PERMANENT_ERROR_STATUS_CODES:
                logger.error(f"LLM request failed with non-retryable status {status_code}: {exc}")
                raise
            # Retry on known transient errors
            if status_code not in RETRYABLE_STATUS_CODES:
                logger.warning(f"LLM request failed with unexpected status {status_code}, will retry...")
            return True
        elif isinstance(exc, requests.ConnectionError):
            logger.warning(f"LLM connection error: {exc}, will retry...")
            return True
        elif isinstance(exc, requests.Timeout):
            logger.warning(f"LLM request timeout: {exc}, will retry...")
            return True
        # For ValueError and other exceptions, allow retry
        return True

    def complete(
        self,
        messages: list[dict[str, str]],
        *,
        temperature: float | None = None,
        max_retries: int = 5,
        retry_delay: float = 2.0,
        operation: str = "unknown",
    ) -> str:
        """Execute a generic chat completion request with retry logic and caching.

        Args:
            messages: Chat messages for the LLM
            temperature: Sampling temperature (default: from HEURISTIC_THRESHOLDS)
            max_retries: Maximum number of retry attempts (default: 5)
            retry_delay: Base delay between retries in seconds (default: 2.0)
            operation: Name of the operation for metrics tracking

        Returns:
            LLM response content

        Raises:
            ValueError: If response is invalid after all retries
            requests.HTTPError: If HTTP error persists after all retries
        """
        start_time = time.time()
        retry_count = 0
        cache_hit = False

        # Use default temperature if not specified
        # Increased from 0.4 to 0.5 for better response quality and creativity
        if temperature is None:
            temperature = 0.5

        # Check cache first if enabled
        cached_response, cache_key = self._check_cache(messages, temperature)
        if cached_response:
            cache_hit = True
            duration = time.time() - start_time

            # Record cache hit metrics
            metrics = LLMCallMetrics(
                operation=operation,
                duration_seconds=duration,
                cache_hit=True,
                success=True,
            )
            get_global_collector().record(metrics)

            return cached_response

        # Apply rate limiting if configured
        if self.rate_limit_delay > 0:
            time.sleep(self.rate_limit_delay)

        payload = {
            "model": self.model or "default-model",
            "messages": messages,
            "temperature": temperature,
        }

        last_exception = None

        for attempt in range(max_retries + 1):
            try:
                response = requests.post(
                    self.endpoint,
                    json=payload,
                    timeout=self.timeout,
                )
                response.raise_for_status()

                content = self._validate_response(response)

                # Success! Log if this was a retry
                if attempt > 0:
                    logger.info(f"LLM request succeeded on attempt {attempt + 1}")
                    retry_count = attempt

                # Extract token usage if available
                prompt_tokens = 0
                completion_tokens = 0
                total_tokens = 0

                try:
                    response_data = response.json()
                    usage = response_data.get("usage", {})
                    prompt_tokens = usage.get("prompt_tokens", 0)
                    completion_tokens = usage.get("completion_tokens", 0)
                    total_tokens = usage.get("total_tokens", 0)
                except (ValueError, KeyError, AttributeError):
                    pass  # Token info not available

                # Record success metrics
                duration = time.time() - start_time
                metrics = LLMCallMetrics(
                    operation=operation,
                    duration_seconds=duration,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=total_tokens,
                    cache_hit=False,
                    success=True,
                    retry_count=retry_count,
                )
                get_global_collector().record(metrics)

                # Save to cache if enabled
                if self.enable_cache and cache_key:
                    save_to_cache(cache_key, content)

                return content

            except (requests.RequestException, ValueError) as exc:
                last_exception = exc
                retry_count = attempt

                # Check if we should retry this error
                self._should_retry_error(exc)

                # Log the error and retry if we have attempts left
                if attempt < max_retries:
                    # Exponential backoff: 2s, 4s, 8s
                    delay = retry_delay * (2 ** attempt)
                    logger.warning(
                        f"LLM request failed (attempt {attempt + 1}/{max_retries + 1}): {exc}. "
                        f"Retrying in {delay}s..."
                    )
                    time.sleep(delay)
                else:
                    logger.error(
                        f"LLM request failed after {max_retries + 1} attempts: {exc}"
                    )

        # Record failure metrics
        duration = time.time() - start_time
        error_type = type(last_exception).__name__ if last_exception else "Unknown"
        metrics = LLMCallMetrics(
            operation=operation,
            duration_seconds=duration,
            cache_hit=False,
            success=False,
            error_type=error_type,
            retry_count=retry_count,
        )
        get_global_collector().record(metrics)

        # If we get here, all retries failed
        raise last_exception  # type: ignore

    def analyze_commit_messages(
        self, commits: list[dict[str, str]], repo: str = ""
    ) -> dict[str, Any]:
        """Analyze commit message quality using LLM with fallback to heuristics.

        Args:
            commits: List of commit dictionaries with 'sha' and 'message' keys
            repo: Repository name in format 'owner/repo' (e.g., 'goonbamm/github-feedback-analysis')
        """
        config = AnalysisConfig(
            analysis_type="commit messages",
            sample_size=LLM_DEFAULTS["sample_size_commits"],
            system_prompt=get_commit_analysis_system_prompt(
                self.web_url,
                repo,
                TEXT_LIMITS['max_samples_mentioned_in_prompt']
            ),
            user_prompt_template=get_commit_analysis_user_prompt(),
            empty_result={
                "good_messages": 0,
                "poor_messages": 0,
                "suggestions": ["커밋 메시지를 분석할 데이터가 없습니다."],
                "examples_good": [],
                "examples_poor": [],
            },
            fallback_method_name="_fallback_commit_analysis",
        )

        result = self._analyze_with_config(commits, config, "commits")

        # Add URLs to examples if not present (for fallback or LLM responses without URLs)
        if repo:
            for example in result.get("examples_good", []):
                if "url" not in example and "sha" in example:
                    example["url"] = f"{self.web_url}/{repo}/commit/{example['sha']}"
            for example in result.get("examples_poor", []):
                if "url" not in example and "sha" in example:
                    example["url"] = f"{self.web_url}/{repo}/commit/{example['sha']}"

        # Map result keys to expected output format
        return {
            "good_messages": result.get("good_count", 0),
            "poor_messages": result.get("poor_count", 0),
            "suggestions": result.get("suggestions", []),
            "examples_good": result.get("examples_good", []),
            "examples_poor": result.get("examples_poor", []),
        }

    def analyze_pr_titles(self, pr_titles: list[dict[str, str]]) -> dict[str, Any]:
        """Analyze pull request title quality using LLM with fallback to heuristics."""
        config = AnalysisConfig(
            analysis_type="PR titles",
            sample_size=LLM_DEFAULTS["sample_size_prs"],
            system_prompt=get_pr_title_analysis_system_prompt(),
            user_prompt_template=get_pr_title_analysis_user_prompt(),
            empty_result={
                "clear_titles": 0,
                "vague_titles": 0,
                "suggestions": ["PR 제목을 분석할 데이터가 없습니다."],
                "examples_good": [],
                "examples_poor": [],
            },
            fallback_method_name="_fallback_pr_title_analysis",
        )

        result = self._analyze_with_config(pr_titles, config, "prs")

        return {
            "clear_titles": result.get("clear_count", 0),
            "vague_titles": result.get("vague_count", 0),
            "suggestions": result.get("suggestions", []),
            "examples_good": result.get("examples_good", []),
            "examples_poor": result.get("examples_poor", []),
        }

    def analyze_review_tone(
        self, review_comments: list[dict[str, str]]
    ) -> dict[str, Any]:
        """Analyze code review tone and style using LLM with fallback to heuristics."""
        config = AnalysisConfig(
            analysis_type="review tone",
            sample_size=LLM_DEFAULTS["sample_size_reviews"],
            system_prompt=get_review_tone_analysis_system_prompt(self.web_url),
            user_prompt_template=get_review_tone_analysis_user_prompt(),
            empty_result={
                "constructive_reviews": 0,
                "harsh_reviews": 0,
                "neutral_reviews": 0,
                "suggestions": ["리뷰 코멘트를 분석할 데이터가 없습니다."],
                "examples_good": [],
                "examples_improve": [],
            },
            fallback_method_name="_fallback_review_tone_analysis",
        )

        result = self._analyze_with_config(review_comments, config, "reviews")

        return {
            "constructive_reviews": result.get("constructive_count", 0),
            "harsh_reviews": result.get("harsh_count", 0),
            "neutral_reviews": result.get("neutral_count", 0),
            "suggestions": result.get("suggestions", []),
            "examples_good": result.get("examples_good", []),
            "examples_improve": result.get("examples_improve", []),
        }

    def analyze_issue_quality(
        self,
        issues: list[dict[str, str]],
        web_url: str = "https://github.com",
        repo: str = "",
    ) -> dict[str, Any]:
        """Analyze issue quality and clarity using LLM with fallback to heuristics.

        Args:
            issues: List of issue dictionaries
            web_url: GitHub web URL for generating issue links
            repo: Repository name in format 'owner/repo'

        Returns:
            Dictionary with issue quality analysis
        """
        config = AnalysisConfig(
            analysis_type="issue quality",
            sample_size=LLM_DEFAULTS["sample_size_issues"],
            system_prompt=get_issue_quality_analysis_system_prompt(web_url=web_url, repo=repo),
            user_prompt_template=get_issue_quality_analysis_user_prompt(),
            empty_result={
                "well_described": 0,
                "poorly_described": 0,
                "suggestions": ["이슈를 분석할 데이터가 없습니다."],
                "examples_good": [],
                "examples_poor": [],
            },
            fallback_method_name="_fallback_issue_analysis",
        )

        result = self._analyze_with_config(issues, config, "issues")

        return {
            "well_described": result.get("well_described_count", 0),
            "poorly_described": result.get("poorly_described_count", 0),
            "suggestions": result.get("suggestions", []),
            "examples_good": result.get("examples_good", []),
            "examples_poor": result.get("examples_poor", []),
        }

    def analyze_personal_development(
        self,
        pr_titles: list[dict[str, str]],
        review_comments: list[dict[str, str]],
        repo: str = "",
    ) -> dict[str, Any]:
        """Analyze personal development from PR titles and review comments using split prompts.

        This method uses three separate LLM calls to reduce hallucination:
        1. Communication quality analysis
        2. Code quality analysis
        3. Growth indicators and overall assessment

        Args:
            pr_titles: List of PR title dictionaries
            review_comments: List of review comment dictionaries
            repo: Repository name

        Returns:
            Dictionary with personal development analysis
        """
        from .prompts import (
            get_communication_analysis_prompt,
            get_code_quality_analysis_prompt,
            get_growth_assessment_prompt,
        )

        if not pr_titles and not review_comments:
            return {
                "strengths": [],
                "improvement_areas": [],
                "growth_indicators": [],
                "overall_assessment": "분석할 데이터가 없습니다.",
                "key_achievements": [],
                "next_focus_areas": [],
            }

        # Build context from PR titles and review comments
        context_lines = []
        context_lines.append(f"Repository: {repo}")
        context_lines.append(f"총 PR 수: {len(pr_titles)}")
        context_lines.append("")

        # Add PR titles with code change information
        # Increased from 50 to 100 PRs for better analysis coverage
        if pr_titles:
            context_lines.append("Pull Request 제목 및 코드 변화:")
            for pr in pr_titles[:100]:  # Limit to 100 PRs
                additions = pr.get('additions', 0)
                deletions = pr.get('deletions', 0)
                total_changes = additions + deletions
                context_lines.append(
                    f"- PR #{pr.get('number', 0)}: {pr.get('title', '')} "
                    f"(작성자: {pr.get('author', '')}, 코드 변화: +{additions}/-{deletions}, 총 {total_changes}줄)"
                )
            context_lines.append("")

        # Add review comments
        # Increased from 30 to 50 comments and from 200 to 400 chars for richer context
        if review_comments:
            context_lines.append(f"리뷰 코멘트 ({len(review_comments)}개):")
            for idx, comment in enumerate(review_comments[:50], 1):  # Limit to 50 comments
                pr_num = comment.get("pr_number", "")
                author = comment.get("author", "")
                body = comment.get("body", "")[:400]  # Truncate long comments
                context_lines.append(f"{idx}. PR #{pr_num} ({author}): {body}")
            context_lines.append("")

        context = "\n".join(context_lines)

        # Calculate early and recent review counts
        midpoint = len(pr_titles) // 2
        early_count = midpoint if midpoint > 0 else 0
        recent_count = len(pr_titles) - midpoint if midpoint > 0 else len(pr_titles)

        try:
            import json as json_module

            # Prepare all three analysis tasks
            comm_messages = [
                {"role": "system", "content": get_communication_analysis_prompt()},
                {"role": "user", "content": f"다음 PR 데이터를 분석해주세요:\n\n{context}"},
            ]

            code_messages = [
                {"role": "system", "content": get_code_quality_analysis_prompt()},
                {"role": "user", "content": f"다음 PR 데이터를 분석해주세요:\n\n{context}"},
            ]

            # Execute communication and code quality analyses in parallel
            console.log("Analyzing communication quality and code quality in parallel...")

            # Increased temperature from 0.4 to 0.6 for better response quality
            # Increased max_retries from 3 to 5 for more robust analysis
            with ThreadPoolExecutor(max_workers=2) as executor:
                # Submit both tasks with operation names for metrics
                comm_future = executor.submit(
                    self.complete, comm_messages, 0.6, 5, 2.0, "personal_dev_communication"
                )
                code_future = executor.submit(
                    self.complete, code_messages, 0.6, 5, 2.0, "personal_dev_code_quality"
                )

                # Wait for both to complete
                comm_content = comm_future.result()
                code_content = code_future.result()

            comm_result = json_module.loads(comm_content)
            code_result = json_module.loads(code_content)

            # Step 3: Analyze growth and overall assessment (depends on previous results)
            console.log("Analyzing growth indicators and overall assessment...")
            # Provide previous analysis results as context
            previous_analysis = f"커뮤니케이션 분석: {len(comm_result.get('strengths', []))}개 강점, {len(comm_result.get('improvement_areas', []))}개 개선점\n"
            previous_analysis += f"코드 품질 분석: {len(code_result.get('strengths', []))}개 강점, {len(code_result.get('improvement_areas', []))}개 개선점\n\n"
            previous_analysis += f"초기 PR 수: {early_count}개\n최근 PR 수: {recent_count}개"

            growth_messages = [
                {"role": "system", "content": get_growth_assessment_prompt()},
                {"role": "user", "content": f"다음 PR 데이터와 이전 분석 결과를 바탕으로 평가해주세요:\n\n{context}\n\n{previous_analysis}"},
            ]
            # Increased temperature from 0.4 to 0.6 for better response quality
            # Increased max_retries from default to 5
            growth_content = self.complete(
                growth_messages, temperature=0.6, max_retries=5, operation="personal_dev_growth"
            )
            growth_result = json_module.loads(growth_content)

            # Merge results
            combined_result = {
                "strengths": comm_result.get("strengths", []) + code_result.get("strengths", []),
                "improvement_areas": comm_result.get("improvement_areas", []) + code_result.get("improvement_areas", []),
                "growth_indicators": growth_result.get("growth_indicators", []),
                "overall_assessment": growth_result.get("overall_assessment", ""),
                "key_achievements": growth_result.get("key_achievements", []),
                "next_focus_areas": growth_result.get("next_focus_areas", []),
            }

            # Validate response quality
            validation_result = LLMResponseValidator.validate_personal_development_response(
                combined_result
            )

            # Log validation results
            if validation_result.warnings:
                console.log(f"⚠️  Response quality warnings ({len(validation_result.warnings)}):")
                for warning in validation_result.warnings[:5]:  # Show first 5 warnings
                    console.log(f"  - {warning}")

            if not validation_result.is_valid:
                console.log(
                    f"⚠️  Response quality score: {validation_result.score:.2f} "
                    f"(threshold: 0.6, issues: {len(validation_result.issues)})"
                )
                for issue in validation_result.issues[:3]:  # Show first 3 issues
                    console.log(f"  - {issue}")
                console.log("Enhancing response with hybrid analysis...")

                # Enhance with hybrid analysis
                enhanced_result = HybridAnalyzer.validate_and_enhance_personal_development(
                    combined_result,
                    validation_result,
                    pr_titles
                )
                return enhanced_result
            else:
                console.log(
                    f"✓ Response validated (quality score: {validation_result.score:.2f})"
                )

            return combined_result
        except Exception as exc:
            console.log(f"Personal development analysis failed: {exc}")
            return {
                "strengths": [],
                "improvement_areas": [],
                "growth_indicators": [],
                "overall_assessment": f"분석 중 오류가 발생했습니다: {str(exc)}",
                "key_achievements": [],
                "next_focus_areas": [],
            }

    def generate_award_summary_quote(
        self,
        awards: list[str],
        highlights: list[str],
        summary: dict[str, str],
    ) -> str:
        """Generate a witty summary quote for the award winner.

        Args:
            awards: List of awards received
            highlights: List of growth highlights
            summary: Summary dictionary with key metrics

        Returns:
            A witty summary quote, or empty string if generation fails
        """
        # Return empty if no data to work with
        if not awards and not highlights and not summary:
            return ""

        try:
            # Build messages
            messages = [
                {
                    "role": "system",
                    "content": get_award_summary_quote_system_prompt(),
                },
                {
                    "role": "user",
                    "content": get_award_summary_quote_user_prompt(awards, highlights, summary),
                },
            ]

            # Call LLM
            response = self.complete(messages)

            # Check for empty response
            if not response or not response.strip():
                logger.warning("Empty response from LLM for award summary quote")
                return ""

            result = json.loads(response)
            quote = result.get("quote", "")

            return quote.strip()

        except (ValueError, requests.RequestException, json.JSONDecodeError) as exc:
            # Log warning but don't fail the report generation
            logger.warning(f"LLM award summary quote generation failed: {exc}")
            console.print(
                "[warning]⚠ 수상자 요약 문구 생성 실패 - 계속 진행합니다[/]",
                style="warning",
            )
            return ""

    # Fallback analysis methods ----------------------------------------

    def _fallback_commit_analysis(self, commits: list[dict[str, str]]) -> dict[str, Any]:
        """Heuristic-based commit message analysis fallback."""
        return CommitMessageAnalyzer.analyze(commits)

    def _fallback_pr_title_analysis(self, prs: list[dict[str, str]]) -> dict[str, Any]:
        """Heuristic-based PR title analysis fallback."""
        return PRTitleAnalyzer.analyze(prs)

    def _fallback_review_tone_analysis(self, reviews: list[dict[str, str]]) -> dict[str, Any]:
        """Heuristic-based review tone analysis fallback."""
        return ReviewToneAnalyzer.analyze(reviews)

    def _fallback_issue_analysis(self, issues: list[dict[str, str]]) -> dict[str, Any]:
        """Heuristic-based issue quality analysis fallback."""
        return IssueQualityAnalyzer.analyze(issues)


__all__ = ["LLMClient"]
