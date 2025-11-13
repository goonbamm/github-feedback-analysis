"""Utility helpers for interacting with Large Language Model endpoints."""

from __future__ import annotations

import hashlib
import json
import logging
import time
from dataclasses import dataclass
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional

import requests

from .console import Console
from .constants import LLM_DEFAULTS, THREAD_POOL_CONFIG
from .models import PullRequestReviewBundle, ReviewPoint, ReviewSummary
from .utils import limit_items, safe_truncate_str, truncate_patch

logger = logging.getLogger(__name__)
console = Console()


# Default values (used when config is not available)
MAX_PATCH_LINES_PER_FILE = LLM_DEFAULTS['max_patch_lines_per_file']
MAX_FILES_WITH_PATCH_SNIPPETS = LLM_DEFAULTS['max_files_with_patch_snippets']

# Cache settings
DEFAULT_CACHE_EXPIRE_DAYS = 7
LLM_CACHE_DIR = Path.home() / ".cache" / "github_feedback" / "llm_cache"


def _get_cache_key(data: Any) -> str:
    """Generate a cache key from input data using SHA256 hash."""
    # Convert data to a stable JSON string
    json_str = json.dumps(data, sort_keys=True, ensure_ascii=False)
    # Generate hash
    return hashlib.sha256(json_str.encode('utf-8')).hexdigest()


def _get_cache_path(cache_key: str) -> Path:
    """Get the file path for a cache key."""
    LLM_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return LLM_CACHE_DIR / f"{cache_key}.json"


def _load_from_cache(cache_key: str, max_age_days: int = DEFAULT_CACHE_EXPIRE_DAYS) -> Optional[str]:
    """Load cached LLM response if it exists and is not expired."""
    cache_path = _get_cache_path(cache_key)

    if not cache_path.exists():
        return None

    # Check cache age
    age_seconds = time.time() - cache_path.stat().st_mtime
    age_days = age_seconds / (24 * 3600)

    if age_days > max_age_days:
        logger.debug(f"Cache expired (age: {age_days:.1f} days)")
        return None

    try:
        with open(cache_path, 'r', encoding='utf-8') as f:
            cached_data = json.load(f)
            logger.debug(f"Cache hit (age: {age_days:.1f} days)")
            return cached_data.get('response')
    except (json.JSONDecodeError, IOError) as exc:
        logger.warning(f"Failed to load cache: {exc}")
        return None


def _save_to_cache(cache_key: str, response: str) -> None:
    """Save LLM response to cache."""
    cache_path = _get_cache_path(cache_key)

    try:
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump({
                'response': response,
                'timestamp': time.time(),
            }, f, ensure_ascii=False, indent=2)
        logger.debug("Saved response to cache")
    except IOError as exc:
        logger.warning(f"Failed to save cache: {exc}")


def with_llm_fallback(fallback_method_name: str) -> Callable:
    """Decorator to add consistent error handling with fallback for LLM analysis methods.

    Args:
        fallback_method_name: Name of the fallback method to call on error

    Returns:
        Decorated function with error handling
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self, data: List[Dict[str, str]]) -> Dict[str, Any]:
            try:
                return func(self, data)
            except (ValueError, requests.RequestException, json.JSONDecodeError) as exc:
                # Fallback to simple heuristics on known errors
                analysis_type = func.__name__.replace('analyze_', '').replace('_', ' ')
                logger.warning(f"LLM {analysis_type} analysis failed: {exc}")
                console.print(
                    f"[warning]⚠ LLM {analysis_type} analysis unavailable - using heuristic analysis[/]",
                    style="warning"
                )
                fallback_method = getattr(self, fallback_method_name)
                # Get the sample data from the first few lines of the function
                # We'll pass the data directly to fallback
                sample_size = 20 if 'commit' in analysis_type or 'pr' in analysis_type else 15
                sample_data = data[:sample_size]
                return fallback_method(sample_data)
        return wrapper
    return decorator


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

    def _build_messages(self, bundle: PullRequestReviewBundle) -> List[Dict[str, str]]:
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
                "content": (
                    "당신은 시니어 소프트웨어 엔지니어로서 코드 리뷰를 수행합니다.\n\n"
                    "다음 원칙을 따르세요:\n"
                    "1. 보안, 성능, 가독성, 유지보수성 순으로 우선순위 평가\n"
                    "2. 각 피드백에 구체적 근거와 개선 방법 제시\n"
                    "3. 긍정적 피드백과 개선점을 균형있게 제공 (최소 1:1 비율)\n"
                    "4. 코드 컨텍스트가 제한적이면 \"전체 컨텍스트 확인 필요\" 명시\n\n"
                    "응답은 반드시 다음 JSON 형식을 따르세요:\n\n"
                    "{\n"
                    '  "overview": "PR의 전반적 평가 (2-3문장)",\n'
                    '  "strengths": [\n'
                    "    {\n"
                    '      "message": "장점 설명",\n'
                    '      "example": "관련 코드나 파일명",\n'
                    '      "impact": "high|medium|low"\n'
                    "    }\n"
                    "  ],\n"
                    '  "improvements": [\n'
                    "    {\n"
                    '      "message": "개선 제안",\n'
                    '      "example": "구체적 코드 예시나 위치",\n'
                    '      "priority": "critical|important|nice-to-have",\n'
                    '      "category": "security|performance|readability|maintainability|testing"\n'
                    "    }\n"
                    "  ]\n"
                    "}\n\n"
                    "각 배열은 최소 1개, 최대 5개 항목을 포함하세요. 모든 응답은 한국어로 작성하세요."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ]

    def _parse_points(self, payload: Iterable[Any]) -> List[ReviewPoint]:
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

    def generate_review(self, bundle: PullRequestReviewBundle) -> ReviewSummary:
        """Invoke the configured LLM endpoint and parse the structured feedback."""

        base_payload = {
            "model": self.model or "default-model",
            "messages": self._build_messages(bundle),
            "temperature": 0.3,
        }

        request_payloads: List[Dict[str, Any]] = [
            base_payload | {"response_format": {"type": "json_object"}}
        ]
        request_payloads.append(base_payload)

        last_error: Exception | None = None
        for request_payload in request_payloads:
            try:
                response = requests.post(
                    self.endpoint,
                    json=request_payload,
                    timeout=self.timeout,
                )
                response.raise_for_status()
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
                error_text = ""
                if exc.response is not None:
                    try:
                        error_text = exc.response.text
                    except Exception:  # pragma: no cover - defensive guard for rare encodings
                        error_text = ""

                last_error = exc
                status_code = exc.response.status_code if exc.response is not None else None
                error_text_lower = error_text.lower()

                if "response_format" in request_payload:
                    if status_code is not None and status_code >= 500:
                        continue
                    if status_code in {400, 404, 415, 422} and (
                        "json_object" in error_text_lower or "response_format" in error_text_lower
                    ):
                        continue
                raise
            except Exception as exc:  # pragma: no cover - network failures already handled elsewhere
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
            "temperature": 0.1,
            "max_tokens": 10,
        }

        # Use shorter timeout for test connection
        test_timeout = THREAD_POOL_CONFIG['test_connection_timeout']
        response = requests.post(
            self.endpoint,
            json=payload,
            timeout=min(self.timeout, test_timeout),
        )
        response.raise_for_status()

        try:
            response_payload = response.json()
        except ValueError as exc:
            raise ValueError("LLM endpoint returned invalid JSON") from exc

        choices = response_payload.get("choices")
        if not choices:
            raise ValueError("LLM endpoint response format is invalid (missing 'choices')")

    def complete(
        self,
        messages: List[Dict[str, str]],
        *,
        temperature: float = 0.3,
        max_retries: int = 3,
        retry_delay: float = 2.0,
    ) -> str:
        """Execute a generic chat completion request with retry logic and caching.

        Args:
            messages: Chat messages for the LLM
            temperature: Sampling temperature
            max_retries: Maximum number of retry attempts (default: 3)
            retry_delay: Base delay between retries in seconds (default: 2.0)

        Returns:
            LLM response content

        Raises:
            ValueError: If response is invalid after all retries
            requests.HTTPError: If HTTP error persists after all retries
        """

        # Check cache first if enabled
        cache_key = None
        if self.enable_cache:
            cache_data = {
                "messages": messages,
                "temperature": temperature,
                "model": self.model,
            }
            cache_key = _get_cache_key(cache_data)
            cached_response = _load_from_cache(cache_key, self.cache_expire_days)
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

                # Success! Log if this was a retry
                if attempt > 0:
                    logger.info(f"LLM request succeeded on attempt {attempt + 1}")

                # Save to cache if enabled
                if self.enable_cache and cache_key:
                    _save_to_cache(cache_key, content)

                return content

            except (requests.RequestException, ValueError) as exc:
                last_exception = exc

                # Define retryable and permanent error status codes
                RETRYABLE_STATUS_CODES = {429, 408, 500, 502, 503, 504}  # Rate limit, timeout, server errors
                PERMANENT_ERROR_STATUS_CODES = {400, 401, 403, 404, 422}  # Bad request, auth, not found

                # Don't retry on certain errors
                if isinstance(exc, requests.HTTPError):
                    status_code = exc.response.status_code
                    # Don't retry on permanent client errors
                    if status_code in PERMANENT_ERROR_STATUS_CODES:
                        logger.error(f"LLM request failed with non-retryable status {status_code}: {exc}")
                        raise
                    # Retry on known transient errors
                    if status_code not in RETRYABLE_STATUS_CODES:
                        logger.warning(f"LLM request failed with unexpected status {status_code}, will retry...")
                elif isinstance(exc, requests.ConnectionError):
                    logger.warning(f"LLM connection error: {exc}, will retry...")
                elif isinstance(exc, requests.Timeout):
                    logger.warning(f"LLM request timeout: {exc}, will retry...")

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
        self, commits: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """Analyze commit message quality using LLM with fallback to heuristics."""
        if not commits:
            return {
                "good_messages": 0,
                "poor_messages": 0,
                "suggestions": ["커밋 메시지를 분석할 데이터가 없습니다."],
                "examples_good": [],
                "examples_poor": [],
            }

        # Sample commits for analysis
        sample_commits = commits[:LLM_DEFAULTS['sample_size_commits']]

        try:
            commit_list = "\n".join([
                f"{i+1}. {safe_truncate_str(commit['message'], 100)} (SHA: {commit['sha'][:7]})"
                for i, commit in enumerate(sample_commits)
            ])

            messages = [
                {
                    "role": "system",
                    "content": (
                        "당신은 Git 커밋 메시지 품질을 평가하는 전문가입니다.\n\n"
                        "다음 기준으로 평가하세요:\n\n"
                        "**좋은 커밋 메시지 기준:**\n"
                        "1. 첫 줄: 50자 이내, 명령형 동사 시작 (Add, Fix, Update, Refactor 등)\n"
                        "2. 본문: 왜(why) 변경했는지 설명 (무엇을 변경했는지는 코드로 알 수 있음)\n"
                        "3. Conventional Commits 형식 권장: `type(scope): subject`\n"
                        "4. Issue/PR 번호 참조 포함\n"
                        "5. 여러 변경사항은 여러 커밋으로 분리\n\n"
                        "**나쁜 커밋 메시지 예:**\n"
                        '- "fix", "update", "wip", "tmp" 같은 단어만 사용\n'
                        "- 변경 내용 나열만 하고 이유 없음\n"
                        "- 너무 길거나 (100자+) 짧음 (10자-)\n\n"
                        "응답 형식:\n"
                        "{\n"
                        '  "good_count": 숫자,\n'
                        '  "poor_count": 숫자,\n'
                        '  "suggestions": [\n'
                        '    "구체적이고 실행 가능한 개선 제안"\n'
                        "  ],\n"
                        '  "examples_good": [\n'
                        "    {\n"
                        '      "sha": "커밋 해시",\n'
                        '      "message": "커밋 메시지",\n'
                        '      "reason": "왜 좋은지 설명"\n'
                        "    }\n"
                        "  ],\n"
                        '  "examples_poor": [\n'
                        "    {\n"
                        '      "sha": "커밋 해시",\n'
                        '      "message": "커밋 메시지",\n'
                        '      "reason": "왜 개선이 필요한지",\n'
                        '      "suggestion": "개선 방법"\n'
                        "    }\n"
                        "  ],\n"
                        '  "trends": {\n'
                        '    "common_patterns": ["발견된 패턴"],\n'
                        '    "improvement_areas": ["개선 영역"]\n'
                        "  }\n"
                        "}\n\n"
                        "최대 20개 샘플만 분석하고, 대표적인 예시를 선정하세요. 모든 응답은 한국어로 작성하세요."
                    ),
                },
                {
                    "role": "user",
                    "content": f"다음 커밋 메시지들을 분석해주세요:\n\n{commit_list}",
                },
            ]

            response = self.complete(messages, temperature=0.3)
            result = json.loads(response)

            return {
                "good_messages": result.get("good_count", 0),
                "poor_messages": result.get("poor_count", 0),
                "suggestions": result.get("suggestions", []),
                "examples_good": result.get("examples_good", []),
                "examples_poor": result.get("examples_poor", []),
            }
        except (ValueError, requests.RequestException, json.JSONDecodeError) as exc:
            # Fallback to simple heuristics on known errors
            logger.warning(f"LLM commit analysis failed: {exc}")
            console.print(
                "[warning]⚠ LLM commit analysis unavailable - using heuristic analysis[/]",
                style="warning"
            )
            return self._fallback_commit_analysis(sample_commits)

    def analyze_pr_titles(self, pr_titles: List[Dict[str, str]]) -> Dict[str, Any]:
        """Analyze pull request title quality using LLM with fallback to heuristics."""
        if not pr_titles:
            return {
                "clear_titles": 0,
                "vague_titles": 0,
                "suggestions": ["PR 제목을 분석할 데이터가 없습니다."],
                "examples_good": [],
                "examples_poor": [],
            }

        # Sample PR titles for analysis
        sample_prs = pr_titles[:LLM_DEFAULTS['sample_size_prs']]

        try:
            pr_list = "\n".join([
                f"{i+1}. #{pr['number']}: {pr['title']}"
                for i, pr in enumerate(sample_prs)
            ])

            messages = [
                {
                    "role": "system",
                    "content": (
                    "당신은 Pull Request 제목 품질을 평가하는 전문가입니다.\n\n"
                    "**좋은 PR 제목 기준:**\n"
                    "1. 길이: 15-80자 (너무 짧거나 길지 않게)\n"
                    "2. 형식: `[타입] 명확한 변경 내용 설명`\n"
                    "   - 타입 예: Feature, Fix, Refactor, Docs, Test, Chore\n"
                    "3. 변경의 범위와 영향 명시\n"
                    "4. 단순 파일명 나열 금지\n"
                    "5. Issue 번호 참조 권장\n\n"
                    "**명확성 체크리스트:**\n"
                    "- [ ] 제목만 읽고도 변경 내용 이해 가능한가?\n"
                    "- [ ] 구체적인 동사 사용했는가?\n"
                    "- [ ] 사용자 관점의 가치가 드러나는가?\n\n"
                    "**나쁜 예:**\n"
                    '- "Update code" (무엇을 왜?)\n'
                    '- "fix" (무엇을 수정?)\n'
                    '- "Implement feature/login/api/..." (구체성 부족)\n\n'
                    "응답 형식:\n"
                    "{\n"
                    '  "clear_count": 숫자,\n'
                    '  "vague_count": 숫자,\n'
                    '  "suggestions": [\n'
                    '    "팀 전체에 적용 가능한 구체적 가이드라인"\n'
                    "  ],\n"
                    '  "examples_good": [\n'
                    "    {\n"
                    '      "number": PR 번호,\n'
                    '      "title": "제목",\n'
                    '      "reason": "왜 명확한지",\n'
                    '      "score": 1-10\n'
                    "    }\n"
                    "  ],\n"
                    '  "examples_poor": [\n'
                    "    {\n"
                    '      "number": PR 번호,\n'
                    '      "title": "제목",\n'
                    '      "reason": "왜 모호한지",\n'
                    '      "suggestion": "개선된 제목 예시"\n'
                    "    }\n"
                    "  ],\n"
                    '  "patterns": {\n'
                    '    "common_types": ["발견된 타입들"],\n'
                    '    "naming_conventions": ["사용중인 컨벤션"]\n'
                    "  }\n"
                    "}\n\n"
                    "모든 응답은 한국어로 작성하세요."
                ),
            },
            {
                "role": "user",
                "content": f"다음 PR 제목들을 분석해주세요:\n\n{pr_list}",
            },
            ]

            response = self.complete(messages, temperature=0.3)
            result = json.loads(response)

            return {
                "clear_titles": result.get("clear_count", 0),
                "vague_titles": result.get("vague_count", 0),
                "suggestions": result.get("suggestions", []),
                "examples_good": result.get("examples_good", []),
                "examples_poor": result.get("examples_poor", []),
            }
        except (ValueError, requests.RequestException, json.JSONDecodeError) as exc:
            # Fallback to simple heuristics on known errors
            logger.warning(f"LLM PR title analysis failed: {exc}")
            console.print(
                "[warning]⚠ LLM PR title analysis unavailable - using heuristic analysis[/]",
                style="warning"
            )
            return self._fallback_pr_title_analysis(sample_prs)

    def analyze_review_tone(
        self, review_comments: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """Analyze code review tone and style using LLM with fallback to heuristics."""
        if not review_comments:
            return {
                "constructive_reviews": 0,
                "harsh_reviews": 0,
                "neutral_reviews": 0,
                "suggestions": ["리뷰 코멘트를 분석할 데이터가 없습니다."],
                "examples_good": [],
                "examples_improve": [],
            }

        # Sample review comments for analysis
        sample_reviews = review_comments[:LLM_DEFAULTS['sample_size_reviews']]

        try:
            review_list = "\n".join([
                f"{i+1}. (PR #{review['pr_number']}, {review['author']}): {review['body'][:200]}"
                for i, review in enumerate(sample_reviews)
            ])

            messages = [
                {
                    "role": "system",
                "content": (
                    "당신은 팀 협업과 커뮤니케이션 전문가입니다.\n"
                    "코드 리뷰 코멘트의 톤을 분석하고 개선 방안을 제시하세요.\n\n"
                    "**평가 기준:**\n\n"
                    "건설적인 리뷰 (Constructive):\n"
                    "- 구체적 문제 지적 + 해결 방법 제안\n"
                    '- 존중하는 표현 사용 ("~하면 어떨까요?", "~를 고려해보세요")\n'
                    "- 코드에 집중, 사람 비판 X\n"
                    "- 긍정적 피드백 포함\n"
                    '- 예: "이 부분을 함수로 분리하면 테스트하기 쉬울 것 같아요."\n\n'
                    "가혹한 리뷰 (Harsh):\n"
                    '- 명령형/단정적 표현 ("이건 잘못됐어요", "다시 해야 합니다")\n'
                    "- 근거 없는 비판\n"
                    "- 작성자 능력 폄하\n"
                    '- 예: "이건 완전히 잘못된 접근입니다."\n\n'
                    "중립적 리뷰 (Neutral):\n"
                    "- 단순 사실 지적, 개선 방안 없음\n"
                    "- 감정적 톤 없음\n"
                    '- 예: "이 함수는 너무 깁니다."\n\n'
                    "**한국 개발 문화 고려사항:**\n"
                    "- 직접적 표현도 맥락에 따라 건설적일 수 있음\n"
                    "- 높임말 사용 여부보다 내용의 구체성이 중요\n"
                    "- 이모지 사용은 긍정적 신호일 수 있음\n\n"
                    "응답 형식:\n"
                    "{\n"
                    '  "constructive_count": 숫자,\n'
                    '  "harsh_count": 숫자,\n'
                    '  "neutral_count": 숫자,\n'
                    '  "suggestions": [\n'
                    '    "팀 전체 커뮤니케이션 개선 제안"\n'
                    "  ],\n"
                    '  "examples_good": [\n'
                    "    {\n"
                    '      "pr_number": PR 번호,\n'
                    '      "author": "작성자",\n'
                    '      "comment": "코멘트 내용",\n'
                    '      "strengths": ["좋은 점들"]\n'
                    "    }\n"
                    "  ],\n"
                    '  "examples_improve": [\n'
                    "    {\n"
                    '      "pr_number": PR 번호,\n'
                    '      "author": "작성자",\n'
                    '      "comment": "원본 코멘트",\n'
                    '      "issues": ["문제점들"],\n'
                    '      "improved_version": "개선된 표현 예시"\n'
                    "    }\n"
                    "  ],\n"
                    '  "team_culture_insights": {\n'
                    '    "positive_patterns": ["발견된 긍정적 패턴"],\n'
                    '    "areas_for_growth": ["개선 영역"]\n'
                    "  }\n"
                    "}\n\n"
                    "각 카테고리에 명확히 분류하고, 경계선상의 경우 맥락을 고려하세요. 모든 응답은 한국어로 작성하세요."
                ),
            },
            {
                "role": "user",
                "content": f"다음 리뷰 코멘트들을 분석해주세요:\n\n{review_list}",
            },
            ]

            response = self.complete(messages, temperature=0.3)
            result = json.loads(response)

            return {
                "constructive_reviews": result.get("constructive_count", 0),
                "harsh_reviews": result.get("harsh_count", 0),
                "neutral_reviews": result.get("neutral_count", 0),
                "suggestions": result.get("suggestions", []),
                "examples_good": result.get("examples_good", []),
                "examples_improve": result.get("examples_improve", []),
            }
        except (ValueError, requests.RequestException, json.JSONDecodeError) as exc:
            # Fallback to simple heuristics on known errors
            logger.warning(f"LLM review tone analysis failed: {exc}")
            console.print(
                "[warning]⚠ LLM review tone analysis unavailable - using heuristic analysis[/]",
                style="warning"
            )
            return self._fallback_review_tone_analysis(sample_reviews)

    def analyze_issue_quality(self, issues: List[Dict[str, str]]) -> Dict[str, Any]:
        """Analyze issue quality and clarity using LLM with fallback to heuristics."""
        if not issues:
            return {
                "well_described": 0,
                "poorly_described": 0,
                "suggestions": ["이슈를 분석할 데이터가 없습니다."],
                "examples_good": [],
                "examples_poor": [],
            }

        # Sample issues for analysis
        sample_issues = issues[:LLM_DEFAULTS['sample_size_issues']]

        try:
            issue_list = "\n".join([
                f"{i+1}. #{issue['number']}: {issue['title']}\n   본문: {issue['body'][:150]}"
                for i, issue in enumerate(sample_issues)
            ])

            messages = [
                {
                    "role": "system",
                "content": (
                    "당신은 프로젝트 관리 전문가로서 GitHub 이슈 품질을 평가합니다.\n\n"
                    "**이슈 타입별 기준:**\n\n"
                    "Bug Report:\n"
                    "- [ ] 명확한 재현 단계\n"
                    "- [ ] 예상 결과 vs 실제 결과\n"
                    "- [ ] 환경 정보 (OS, 버전 등)\n"
                    "- [ ] 에러 메시지나 스크린샷\n"
                    "- [ ] 영향 범위\n\n"
                    "Feature Request:\n"
                    "- [ ] 해결하려는 문제 설명\n"
                    "- [ ] 제안하는 솔루션\n"
                    "- [ ] 대안 고려사항\n"
                    "- [ ] 사용자 시나리오\n"
                    "- [ ] 우선순위 근거\n\n"
                    "일반 이슈:\n"
                    "- [ ] 명확한 제목 (타입 포함)\n"
                    "- [ ] 상세한 설명 (단순 요청 이상)\n"
                    "- [ ] 라벨이나 마일스톤 설정 가능성\n"
                    "- [ ] 관련 이슈/PR 링크\n\n"
                    "**품질 평가:**\n"
                    "- 잘 작성됨: 위 체크리스트 70% 이상 충족\n"
                    "- 개선 필요: 체크리스트 50% 미만 또는 핵심 정보 누락\n\n"
                    "응답 형식:\n"
                    "{\n"
                    '  "well_described_count": 숫자,\n'
                    '  "poorly_described_count": 숫자,\n'
                    '  "type_breakdown": {\n'
                    '    "bug": 숫자,\n'
                    '    "feature": 숫자,\n'
                    '    "question": 숫자,\n'
                    '    "other": 숫자\n'
                    "  },\n"
                    '  "suggestions": [\n'
                    '    "이슈 템플릿 개선 제안",\n'
                    '    "작성 가이드라인"\n'
                    "  ],\n"
                    '  "examples_good": [\n'
                    "    {\n"
                    '      "number": 이슈 번호,\n'
                    '      "title": "제목",\n'
                    '      "type": "bug|feature|other",\n'
                    '      "strengths": ["잘된 점들"],\n'
                    '      "completeness_score": 1-10\n'
                    "    }\n"
                    "  ],\n"
                    '  "examples_poor": [\n'
                    "    {\n"
                    '      "number": 이슈 번호,\n'
                    '      "title": "제목",\n'
                    '      "missing_elements": ["누락된 요소들"],\n'
                    '      "suggestion": "개선 방법"\n'
                    "    }\n"
                    "  ],\n"
                    '  "template_recommendations": [\n'
                    '    "프로젝트에 권장하는 이슈 템플릿 형식"\n'
                    "  ]\n"
                    "}\n\n"
                    "모든 응답은 한국어로 작성하세요."
                ),
            },
            {
                "role": "user",
                "content": f"다음 이슈들을 분석해주세요:\n\n{issue_list}",
            },
            ]

            response = self.complete(messages, temperature=0.3)
            result = json.loads(response)

            return {
                "well_described": result.get("well_described_count", 0),
                "poorly_described": result.get("poorly_described_count", 0),
                "suggestions": result.get("suggestions", []),
                "examples_good": result.get("examples_good", []),
                "examples_poor": result.get("examples_poor", []),
            }
        except (ValueError, requests.RequestException, json.JSONDecodeError) as exc:
            # Fallback to simple heuristics on known errors
            logger.warning(f"LLM issue analysis failed: {exc}")
            console.print(
                "[warning]⚠ LLM issue analysis unavailable - using heuristic analysis[/]",
                style="warning"
            )
            return self._fallback_issue_analysis(sample_issues)

    # Fallback analysis methods ----------------------------------------

    def _fallback_commit_analysis(self, commits: List[Dict[str, str]]) -> Dict[str, Any]:
        """Enhanced heuristic-based commit message analysis."""
        good_count = 0
        poor_count = 0
        examples_good = []
        examples_poor = []

        # Enhanced patterns
        good_patterns = [
            r'^(feat|fix|docs|style|refactor|test|chore|perf|ci|build|revert)(\(.+\))?: .+',  # Conventional Commits
            r'^(Add|Fix|Update|Refactor|Remove|Implement|Improve|Optimize) [A-Z].+',  # Capitalized imperative
            r'^[A-Z][a-z]+ .+ (#\d+|issue|pr)',  # With issue/PR reference
        ]

        poor_patterns = [
            r'^(wip|tmp|test|debug|asdf|aaa|zzz)',  # Work-in-progress markers
            r'^fix$|^update$|^bug$',  # Too vague
            r'^.{1,5}$',  # Too short (1-5 chars)
            r'^.{150,}',  # Too long (150+ chars)
        ]

        for commit in commits:
            message = commit["message"].strip()
            lines = message.split("\n")
            first_line = lines[0] if lines else ""

            # Enhanced scoring
            score = 0
            issues = []

            # Check length
            if 10 <= len(first_line) <= 72:
                score += 1
            elif len(first_line) < 10:
                issues.append("메시지가 너무 짧습니다")
            elif len(first_line) > 100:
                issues.append("첫 줄이 너무 깁니다")

            # Check for good patterns
            import re
            for pattern in good_patterns:
                if re.match(pattern, first_line, re.IGNORECASE):
                    score += 2
                    break

            # Check for poor patterns
            for pattern in poor_patterns:
                if re.match(pattern, first_line.lower()):
                    score -= 2
                    issues.append("모호하거나 임시 메시지입니다")
                    break

            # Check for body (explains why)
            if len(lines) > 2 and len(lines[2].strip()) > 20:
                score += 1

            # Classify based on score
            is_good = score >= 2

            if is_good:
                good_count += 1
                if len(examples_good) < 3:
                    examples_good.append({
                        "message": first_line,
                        "sha": commit["sha"][:7],
                        "reason": "적절한 길이와 형식을 갖추었습니다"
                    })
            else:
                poor_count += 1
                if len(examples_poor) < 3:
                    examples_poor.append({
                        "message": first_line,
                        "sha": commit["sha"][:7],
                        "reason": ", ".join(issues) if issues else "개선이 필요합니다",
                        "suggestion": "Conventional Commits 형식을 사용해보세요 (예: feat: 새 기능 추가)"
                    })

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

    def _fallback_pr_title_analysis(self, prs: List[Dict[str, str]]) -> Dict[str, Any]:
        """Enhanced heuristic-based PR title analysis."""
        import re

        clear_count = 0
        vague_count = 0
        examples_good = []
        examples_poor = []

        # Enhanced patterns
        clear_patterns = [
            r'^\[(feat|fix|docs|style|refactor|test|chore|perf|ci|build)\].+',  # [type] format
            r'^(feat|fix|docs|style|refactor|test|chore|perf|ci|build):.+',  # type: format
            r'^(Add|Fix|Update|Refactor|Remove|Implement|Improve) .+',  # Imperative verb
        ]

        vague_keywords = [
            'update', 'fix', 'change', 'modify', 'edit', 'misc', 'various',
            'stuff', 'things', 'code', 'work'
        ]

        for pr in prs:
            title = pr["title"].strip()
            score = 0
            reasons = []

            # Check length
            if 15 <= len(title) <= 80:
                score += 1
            else:
                if len(title) < 15:
                    reasons.append("제목이 너무 짧습니다")
                else:
                    reasons.append("제목이 너무 깁니다")

            # Check for clear patterns
            has_clear_pattern = False
            for pattern in clear_patterns:
                if re.match(pattern, title, re.IGNORECASE):
                    score += 2
                    has_clear_pattern = True
                    break

            # Check for vague keywords (only first word)
            first_word = title.split()[0].lower() if title.split() else ""
            if first_word in vague_keywords and not has_clear_pattern:
                score -= 1
                reasons.append("너무 일반적인 단어로 시작합니다")

            # Check for specificity (has specific terms, not just generic words)
            if len(title.split()) >= 4:  # At least 4 words
                score += 1

            # Classify
            is_clear = score >= 2

            if is_clear:
                clear_count += 1
                if len(examples_good) < 3:
                    examples_good.append({
                        "number": pr["number"],
                        "title": title,
                        "reason": "명확하고 설명적인 제목입니다",
                        "score": min(10, score * 3)
                    })
            else:
                vague_count += 1
                if len(examples_poor) < 3:
                    examples_poor.append({
                        "number": pr["number"],
                        "title": title,
                        "reason": ", ".join(reasons) if reasons else "제목이 모호합니다",
                        "suggestion": f"[{first_word if first_word in ['feat', 'fix', 'docs'] else 'feat'}] {title if len(title) > 10 else title + ' - 구체적인 변경 내용 설명'}"
                    })

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

    def _fallback_review_tone_analysis(
        self, reviews: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """Simple heuristic-based review tone analysis."""
        constructive_count = len(reviews)
        harsh_count = 0
        neutral_count = 0

        return {
            "constructive_reviews": constructive_count,
            "harsh_reviews": harsh_count,
            "neutral_reviews": neutral_count,
            "suggestions": [
                "리뷰 코멘트는 건설적이고 존중하는 톤을 유지하세요.",
                "구체적인 개선 제안을 포함하세요.",
                "긍정적인 피드백도 함께 제공하세요.",
            ],
            "examples_good": [],
            "examples_improve": [],
        }

    def _fallback_issue_analysis(self, issues: List[Dict[str, str]]) -> Dict[str, Any]:
        """Enhanced heuristic-based issue quality analysis."""
        import re

        well_described = 0
        poorly_described = 0
        examples_good = []
        examples_poor = []

        for issue in issues:
            body = issue.get("body", "").strip()
            title = issue.get("title", "").strip()
            score = 0
            strengths = []
            missing = []

            # Check body length
            if len(body) > 200:
                score += 2
                strengths.append("상세한 설명")
            elif len(body) > 100:
                score += 1
            else:
                missing.append("본문이 너무 짧습니다")

            # Check for structured information
            if re.search(r'(steps to reproduce|재현 단계|how to reproduce)', body, re.IGNORECASE):
                score += 2
                strengths.append("재현 단계 포함")

            if re.search(r'(expected|actual|예상|실제)', body, re.IGNORECASE):
                score += 1
                strengths.append("예상/실제 결과 비교")

            if re.search(r'(environment|version|os|browser|환경)', body, re.IGNORECASE):
                score += 1
                strengths.append("환경 정보 포함")

            if re.search(r'(screenshot|image|!\\[|스크린샷)', body, re.IGNORECASE):
                score += 1
                strengths.append("스크린샷/이미지 첨부")

            # Check for code blocks
            if '```' in body or '`' in body:
                score += 1
                strengths.append("코드 예시 포함")

            # Check for links/references
            if re.search(r'(#\\d+|http|related|참고)', body, re.IGNORECASE):
                score += 1

            # Detect common missing elements
            if score < 3:
                if not re.search(r'(steps|재현|how to)', body, re.IGNORECASE):
                    missing.append("재현 단계")
                if not re.search(r'(expected|actual|예상|실제)', body, re.IGNORECASE):
                    missing.append("예상/실제 결과")
                if not re.search(r'(environment|version|환경)', body, re.IGNORECASE):
                    missing.append("환경 정보")

            # Classify
            is_good = score >= 4

            if is_good:
                well_described += 1
                if len(examples_good) < 3:
                    examples_good.append({
                        "number": issue["number"],
                        "title": title,
                        "type": self._detect_issue_type(title, body),
                        "strengths": strengths[:3],  # Top 3 strengths
                        "completeness_score": min(10, score)
                    })
            else:
                poorly_described += 1
                if len(examples_poor) < 3:
                    examples_poor.append({
                        "number": issue["number"],
                        "title": title,
                        "missing_elements": missing,
                        "suggestion": "이슈 템플릿을 사용하거나 재현 단계, 예상/실제 결과, 환경 정보를 추가하세요."
                    })

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

    def _detect_issue_type(self, title: str, body: str) -> str:
        """Detect issue type from title and body."""
        import re
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
