"""Utility helpers for interacting with Large Language Model endpoints."""

from __future__ import annotations

import hashlib
import json
import logging
import re
import time
from dataclasses import dataclass
from functools import wraps
from itertools import islice
from pathlib import Path
from typing import Any, Callable

import requests

from .console import Console
from .constants import HEURISTIC_THRESHOLDS, LLM_DEFAULTS, TEXT_LIMITS, THREAD_POOL_CONFIG
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
from .utils import limit_items, safe_truncate_str, truncate_patch

logger = logging.getLogger(__name__)
console = Console()


# Default values (used when config is not available)
MAX_PATCH_LINES_PER_FILE = LLM_DEFAULTS['max_patch_lines_per_file']
MAX_FILES_WITH_PATCH_SNIPPETS = LLM_DEFAULTS['max_files_with_patch_snippets']


# ============================================================================
# Helper Classes for Heuristic Analysis
# ============================================================================

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

        Returns:
            tuple of (is_good, good_count_delta, poor_count_delta)
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

        Returns:
            tuple of (score, issues_list)
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
    def check_patterns(text: str, patterns: list[str], flags=0) -> bool:
        """Check if text matches any of the given regex patterns."""
        return any(re.match(pattern, text, flags) for pattern in patterns)

    @staticmethod
    def search_patterns(text: str, patterns: list[str], flags=0) -> bool:
        """Check if text contains any of the given regex patterns."""
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
            tuple of (good_count, poor_count, examples_good, examples_poor)
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

# Cache settings
DEFAULT_CACHE_EXPIRE_DAYS = 7
LLM_CACHE_DIR = Path.home() / ".cache" / "github_feedback" / "llm_cache"

# HTTP Status codes for retry logic
RETRYABLE_STATUS_CODES = frozenset({429, 408, 500, 502, 503, 504})  # Rate limit, timeout, server errors
PERMANENT_ERROR_STATUS_CODES = frozenset({400, 401, 403, 404, 422})  # Bad request, auth, not found


def _get_cache_key(data: Any) -> str:
    """Generate a cache key from input data using SHA256 hash."""
    # Convert data to a stable JSON string
    json_str = json.dumps(data, sort_keys=True, ensure_ascii=False)
    # Generate hash
    return hashlib.sha256(json_str.encode("utf-8")).hexdigest()


def _get_cache_path(cache_key: str) -> Path:
    """Get the file path for a cache key.

    Args:
        cache_key: Cache key hash

    Returns:
        Path to cache file

    Raises:
        OSError: If cache directory creation fails
    """
    try:
        LLM_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    except PermissionError as exc:
        logger.warning(f"Permission denied creating cache directory: {exc}")
        raise
    except OSError as exc:
        logger.warning(f"Failed to create cache directory: {exc}")
        raise
    return LLM_CACHE_DIR / f"{cache_key}.json"


def _load_from_cache(cache_key: str, max_age_days: int = DEFAULT_CACHE_EXPIRE_DAYS) -> str | None:
    """Load cached LLM response if it exists and is not expired."""
    cache_path = _get_cache_path(cache_key)

    if not cache_path.exists():
        return None

    # Check cache age
    age_seconds = time.time() - cache_path.stat().st_mtime
    from github_feedback.constants import SECONDS_PER_DAY
    age_days = age_seconds / SECONDS_PER_DAY

    if age_days > max_age_days:
        logger.debug(f"Cache expired (age: {age_days:.1f} days)")
        return None

    try:
        with open(cache_path, "r", encoding="utf-8") as f:
            cached_data = json.load(f)
            logger.debug(f"Cache hit (age: {age_days:.1f} days)")
            return cached_data.get("response")
    except (json.JSONDecodeError, IOError, PermissionError) as exc:
        logger.warning(f"Failed to load cache: {exc}")
        # Delete corrupt cache file
        try:
            cache_path.unlink(missing_ok=True)
        except OSError:
            pass
        return None


def _save_to_cache(cache_key: str, response: str) -> None:
    """Save LLM response to cache.

    Args:
        cache_key: Cache key hash
        response: LLM response to cache

    Note:
        Errors are logged but not raised to avoid disrupting the main workflow
    """
    try:
        cache_path = _get_cache_path(cache_key)
    except OSError as exc:
        logger.warning(f"Failed to get cache path: {exc}")
        return

    try:
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "response": response,
                    "timestamp": time.time(),
                },
                f,
                ensure_ascii=False,
                indent=2,
            )
        logger.debug("Saved response to cache")
    except PermissionError as exc:
        logger.warning(f"Permission denied writing cache file: {exc}")
    except OSError as exc:
        if exc.errno == 28:  # ENOSPC - No space left on device
            logger.warning(f"No space left on device for cache: {exc}")
        else:
            logger.warning(f"Failed to save cache: {exc}")
    except (TypeError, ValueError) as exc:
        logger.warning(f"Failed to serialize cache data: {exc}")


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
        cache_key = _get_cache_key(cache_data)
        cached_response = _load_from_cache(cache_key, self.cache_expire_days)

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
        max_retries: int = 3,
        retry_delay: float = 2.0,
    ) -> str:
        """Execute a generic chat completion request with retry logic and caching.

        Args:
            messages: Chat messages for the LLM
            temperature: Sampling temperature (default: from HEURISTIC_THRESHOLDS)
            max_retries: Maximum number of retry attempts (default: 3)
            retry_delay: Base delay between retries in seconds (default: 2.0)

        Returns:
            LLM response content

        Raises:
            ValueError: If response is invalid after all retries
            requests.HTTPError: If HTTP error persists after all retries
        """
        # Use default temperature if not specified
        if temperature is None:
            temperature = HEURISTIC_THRESHOLDS['llm_temperature']

        # Check cache first if enabled
        cached_response, cache_key = self._check_cache(messages, temperature)
        if cached_response:
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

                # Save to cache if enabled
                if self.enable_cache and cache_key:
                    _save_to_cache(cache_key, content)

                return content

            except (requests.RequestException, ValueError) as exc:
                last_exception = exc

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
            system_prompt=get_review_tone_analysis_system_prompt(),
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

    def analyze_issue_quality(self, issues: list[dict[str, str]]) -> dict[str, Any]:
        """Analyze issue quality and clarity using LLM with fallback to heuristics."""
        config = AnalysisConfig(
            analysis_type="issue quality",
            sample_size=LLM_DEFAULTS["sample_size_issues"],
            system_prompt=get_issue_quality_analysis_system_prompt(),
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
        """Enhanced heuristic-based commit message analysis using helper class."""
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
            score, issues = self._score_commit_message(
                first_line, lines, good_patterns, poor_patterns,
                min_len, max_len, too_long, min_body_len
            )
            return score, (first_line, issues)

        # Define example formatters
        def good_example_fn(commit, metadata):
            first_line, _ = metadata
            # Build detailed reason
            reasons = []
            reasons.append(f"적절한 길이({len(first_line)}자)로 가독성이 좋습니다.")
            if re.match(r'^(feat|fix|docs|style|refactor|test|chore|perf|ci|build|revert)', first_line, re.IGNORECASE):
                reasons.append("Conventional Commits 형식을 따라 타입이 명확합니다.")
            if re.match(r'^(Add|Fix|Update|Refactor|Remove|Implement|Improve|Optimize)', first_line):
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
            # Build detailed reason with specific issues
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

            # Build detailed suggestion
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

    def _score_commit_message(
        self, first_line: str, lines: list[str],
        good_patterns: list[str], poor_patterns: list[str],
        min_len: int, max_len: int, too_long: int, min_body_len: int
    ) -> tuple[int, list[str]]:
        """Score a commit message and return score with issues list."""
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

    def _fallback_pr_title_analysis(self, prs: list[dict[str, str]]) -> dict[str, Any]:
        """Enhanced heuristic-based PR title analysis using helper class."""
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
            score, reasons = self._score_pr_title(
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

    def _score_pr_title(
        self, title: str, clear_patterns: list[str], vague_keywords: set[str],
        min_len: int, max_len: int, min_words: int
    ) -> tuple[int, list[str]]:
        """Score a PR title and return score with reasons list."""
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

    def _fallback_review_tone_analysis(
        self, reviews: list[dict[str, str]]
    ) -> dict[str, Any]:
        """Enhanced heuristic-based review tone analysis using helper class."""
        # Patterns for classification
        constructive_patterns = [
            r'어떨까요|고려해|제안|추천|생각해보',  # 제안형 표현
            r'같아요|것 같|보입니다',  # 부드러운 표현
            r'해보면|시도해|시험해',  # 시도 제안
            r'\?',  # 질문형
            r'좋을 것|나을 것|더 좋',  # 긍정적 제안
            r'예시|예를 들어|이렇게|다음과 같이',  # 구체적 설명
            r'👍|✅|💯|🎉|😊|👏',  # 긍정 이모지
        ]

        harsh_patterns = [
            r'잘못|틀렸|오류|에러(?!:)|문제(?!를 해결)',  # 부정적 직접 지적
            r'다시|반드시|꼭|절대|필수',  # 명령형
            r'왜|이유(?! 없)',  # 추궁형
            r'(?<!더 )나쁨|형편없|최악',  # 부정적 평가
            r'이해(?! 가능|할 수)',  # 이해 부족 지적
        ]

        positive_indicators = [
            r'좋|훌륭|멋|잘|감사|고마|수고',  # 긍정적 단어
            r'명확|깔끔|간결|효율|효과',  # 긍정적 평가
            r'LGTM|looks good|nice|great|excellent',  # 영어 긍정
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
                if re.search(r'어떨까요|고려해|제안|추천', body, re.IGNORECASE):
                    strengths.append("제안형 표현을 사용하여 존중하는 톤을 유지합니다")
                if re.search(r'예시|예를 들어|이렇게|다음과 같이', body, re.IGNORECASE):
                    strengths.append("구체적인 예시를 제공하여 이해를 돕습니다")
                if re.search(r'👍|✅|💯|🎉|😊|👏', body):
                    strengths.append("이모지를 활용하여 긍정적인 분위기를 조성합니다")

            # Check for harsh patterns
            harsh_matches = sum(1 for p in harsh_patterns if re.search(p, body, re.IGNORECASE))
            if harsh_matches > 0:
                score -= harsh_matches * 2
                if re.search(r'잘못|틀렸|오류', body, re.IGNORECASE):
                    issues.append("부정적인 직접 지적으로 상대방의 감정을 상하게 할 수 있습니다")
                if re.search(r'다시|반드시|꼭|절대|필수', body, re.IGNORECASE):
                    issues.append("명령형 표현으로 강압적으로 느껴질 수 있습니다")

            # Check for positive indicators
            positive_matches = sum(1 for p in positive_indicators if re.search(p, body, re.IGNORECASE))
            if positive_matches > 0:
                score += positive_matches
                if re.search(r'좋|훌륭|멋|잘|감사|고마|수고', body, re.IGNORECASE):
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
                    # Replace harsh words with softer alternatives
                    improved = re.sub(r'잘못', '개선이 필요한 부분', improved, flags=re.IGNORECASE)
                    improved = re.sub(r'다시\s+(\w+)', r'\1하면 어떨까요', improved)
                    improved = re.sub(r'반드시|꼭', '~하면 좋을 것 같습니다', improved)

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
        if len([r for r in reviews if re.search(r'👍|✅|💯|🎉|😊|👏', r.get("body", ""))]) < len(reviews) * 0.3:
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

    def _fallback_issue_analysis(self, issues: list[dict[str, str]]) -> dict[str, Any]:
        """Enhanced heuristic-based issue quality analysis using helper class."""
        body_short = HEURISTIC_THRESHOLDS['issue_body_short']
        body_detailed = HEURISTIC_THRESHOLDS['issue_body_detailed']
        good_score = HEURISTIC_THRESHOLDS['issue_good_score']

        # Define scoring function
        def score_fn(issue):
            body = issue.get("body", "").strip()
            title = issue.get("title", "").strip()
            score, strengths, missing = self._score_issue_quality(
                body, body_short, body_detailed, good_score
            )
            return score, (title, body, strengths, missing)

        # Define example formatters
        def good_example_fn(issue, metadata):
            title, body, strengths, _ = metadata
            return {
                "number": issue["number"],
                "title": title,
                "type": self._detect_issue_type(title, body),
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

    def _score_issue_quality(
        self, body: str, body_short: int, body_detailed: int, good_score: int
    ) -> tuple[int, list[str], list[str]]:
        """Score issue quality and return score, strengths, and missing elements."""
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
        if re.search(r'(#\\d+|http|related|참고)', body, re.IGNORECASE):
            score += 1

        return score, strengths, missing

    def _detect_issue_type(self, title: str, body: str) -> str:
        """Detect issue type from title and body."""
        text = (title + " " + body).lower()

        if re.search(r'\b(bug|error|crash|fail|broken|issue)\b', text):
            return "bug"
        elif re.search(r'\b(feature|enhancement|improve|add|request)\b', text):
            return "feature"
        elif re.search(r'\b(question|how|why|documentation|docs)\b', text):
            return "question"
        else:
            return "other"


__all__ = ["LLMClient"]
