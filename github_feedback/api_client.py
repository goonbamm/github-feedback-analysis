"""GitHub API client with Repository pattern."""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union

import requests
import requests_cache

from .config import Config
from .console import Console
from .constants import HTTP_STATUS, RETRY_CONFIG
from .exceptions import ApiError, AuthenticationError, ConfigurationError

logger = logging.getLogger(__name__)
console = Console()

# Type variable for generic response types
T = TypeVar('T', List[Dict[str, Any]], Dict[str, Any])


class GitHubApiClient:
    """Repository pattern wrapper around GitHub REST API.

    This class handles:
    - Authentication
    - Request building and execution
    - Pagination
    - Error handling
    """

    def __init__(
        self,
        config: Config,
        session: Optional[requests.Session] = None,
        enable_cache: bool = True,
        cache_expire_after: int = 3600,
    ):
        """Initialize GitHub API client.

        Args:
            config: Configuration object with PAT and API URL
            session: Optional requests session for connection pooling
            enable_cache: Whether to enable request caching (default: True)
            cache_expire_after: Cache expiration time in seconds (default: 3600)

        Raises:
            ConfigurationError: If PAT is not configured
        """
        self.config = config
        self.enable_cache = enable_cache
        self.cache_expire_after = cache_expire_after
        self.session = session
        self._headers: Dict[str, str] = {}

        pat = self.config.get_pat()
        if not pat:
            raise ConfigurationError(
                "Authentication PAT is not configured. Run `ghf init` first."
            )

        self._headers = {
            "Authorization": f"Bearer {pat}",
            "Accept": "application/vnd.github+json",
        }

    def _get_session(self) -> requests.Session:
        """Get or create requests session with optional caching.

        Returns:
            Configured requests session (cached or regular)
        """
        if self.session is None:
            if self.enable_cache:
                # Create cache directory in user's home config
                cache_dir = Path.home() / ".cache" / "github_feedback"
                cache_dir.mkdir(parents=True, exist_ok=True)
                cache_path = cache_dir / "api_cache"

                # Create cached session
                self.session = requests_cache.CachedSession(
                    cache_name=str(cache_path),
                    backend="sqlite",
                    expire_after=self.cache_expire_after,
                    allowable_codes=[200, 301, 302, 304],
                    # Don't cache POST/PUT/DELETE/PATCH requests
                    allowable_methods=["GET", "HEAD"],
                )
                logger.debug(
                    f"Initialized cached session (expire_after={self.cache_expire_after}s)"
                )
            else:
                self.session = requests.Session()
                logger.debug("Initialized regular session (caching disabled)")

            self.session.headers.update(self._headers)
        return self.session

    def _build_api_url(self, path: str) -> str:
        """Build full API URL from path.

        Args:
            path: API endpoint path

        Returns:
            Full API URL

        Raises:
            ValueError: If path is empty or invalid
        """
        if not path or not path.strip():
            raise ValueError("API path cannot be empty")

        base = self.config.server.api_url.rstrip("/")
        return f"{base}/{path.lstrip('/')}"

    def _get_timeout(self) -> int:
        """Get API timeout from config.

        Returns:
            Timeout in seconds
        """
        timeout = getattr(self.config, "api", None)
        return timeout.timeout if timeout else 30

    def _get_max_retries(self) -> int:
        """Get max retries from config.

        Returns:
            Maximum number of retries
        """
        api_config = getattr(self.config, "api", None)
        return api_config.max_retries if api_config else 3

    def _display_rate_limit_info(self, response: requests.Response) -> None:
        """Display rate limit information from response headers.

        Args:
            response: HTTP response with rate limit headers
        """
        headers = response.headers
        remaining = headers.get('X-RateLimit-Remaining', 'unknown')
        reset_time = headers.get('X-RateLimit-Reset', 'unknown')

        if reset_time != 'unknown':
            import datetime
            try:
                reset_dt = datetime.datetime.fromtimestamp(int(reset_time))
                reset_str = reset_dt.strftime('%H:%M:%S')
                console.print(
                    f"[warning]⚠ Rate limited. Resets at: {reset_str} "
                    f"(Remaining: {remaining})[/]",
                    style="warning"
                )
                return
            except (ValueError, TypeError):
                pass

        console.print(
            f"[warning]⚠ Rate limited. Remaining: {remaining}[/]",
            style="warning"
        )

    def _is_rate_limited(self, exc: requests.HTTPError) -> bool:
        """Check if exception is due to rate limiting.

        Args:
            exc: HTTP error exception

        Returns:
            True if rate limited
        """
        if exc.response is None:
            return False

        status_code = exc.response.status_code
        if status_code in (403, 429):
            self._display_rate_limit_info(exc.response)
            return True
        return False

    def _should_retry(self, exc: Exception) -> bool:
        """Determine if request should be retried based on exception.

        Args:
            exc: Exception that occurred

        Returns:
            True if request should be retried
        """
        # Retry on network errors
        if isinstance(exc, (requests.ConnectionError, requests.Timeout)):
            return True

        # Retry on HTTP errors with retryable status codes
        if isinstance(exc, requests.HTTPError):
            if exc.response is not None:
                status_code = exc.response.status_code

                # Display rate limit info for rate limit errors
                if status_code in (403, 429):
                    self._display_rate_limit_info(exc.response)

                return status_code in HTTP_STATUS['retryable_errors']

        return False

    def _execute_with_retry(
        self,
        path: str,
        params: Optional[Dict[str, Any]],
        validator: Callable[[Any], bool],
        expected_type_name: str,
    ) -> Union[List[Dict[str, Any]], Dict[str, Any]]:
        """Execute API request with retry logic and response validation.

        Args:
            path: API endpoint path
            params: Optional query parameters
            validator: Function to validate response type
            expected_type_name: Name of expected type for error messages

        Returns:
            Validated JSON response

        Raises:
            AuthenticationError: If authentication fails
            ApiError: If request fails after retries or validation fails
        """
        logger.debug(f"Requesting from {path}")
        max_retries = self._get_max_retries()
        last_exception = None

        for attempt in range(max_retries + 1):
            try:
                response = self._get_session().get(
                    self._build_api_url(path),
                    params=params,
                    timeout=self._get_timeout(),
                )

                if response.status_code == HTTP_STATUS['unauthorized']:
                    raise AuthenticationError("GitHub API rejected the provided PAT")

                response.raise_for_status()

                # Check for empty response before attempting JSON decode
                if not response.content or not response.content.strip():
                    logger.error(
                        f"Empty response from {path}. "
                        f"Status: {response.status_code}, "
                        f"Content-Type: {response.headers.get('content-type', 'unknown')}"
                    )
                    raise ApiError(
                        f"Empty response from {path}"
                    )

                try:
                    payload = response.json()
                except json.JSONDecodeError as json_exc:
                    # Log response details for debugging
                    logger.error(
                        f"Failed to decode JSON from {path}. "
                        f"Status: {response.status_code}, "
                        f"Content-Type: {response.headers.get('content-type', 'unknown')}, "
                        f"Content length: {len(response.content)}, "
                        f"Content preview: {response.text[:200]}"
                    )
                    raise ApiError(
                        f"Invalid JSON response from {path}: {json_exc}"
                    ) from json_exc

                if not validator(payload):
                    raise ApiError(
                        f"Expected {expected_type_name} response from {path}, "
                        f"got {type(payload).__name__}"
                    )

                return payload

            except requests.HTTPError as exc:
                last_exception = exc
                if not self._should_retry(exc):
                    status_code = exc.response.status_code if exc.response else None
                    raise ApiError(f"API request failed: {path}", status_code) from exc

            except requests.RequestException as exc:
                last_exception = exc
                if not self._should_retry(exc):
                    raise ApiError(f"Network error for {path}: {exc}") from exc

            # Exponential backoff before retry
            if attempt < max_retries:
                backoff_base = RETRY_CONFIG['backoff_base']
                sleep_time = backoff_base ** attempt  # 1s, 2s, 4s
                logger.debug(
                    f"Retrying {path} after {sleep_time}s "
                    f"(attempt {attempt + 1}/{max_retries})"
                )
                time.sleep(sleep_time)

        # All retries exhausted
        raise ApiError(
            f"Request failed after {max_retries} retries: {path}"
        ) from last_exception

    def request_list(
        self, path: str, params: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Execute API request expecting list response with retry logic.

        Args:
            path: API endpoint path
            params: Optional query parameters

        Returns:
            List of JSON objects

        Raises:
            AuthenticationError: If authentication fails
            ApiError: If request fails after retries
        """
        result = self._execute_with_retry(
            path=path,
            params=params,
            validator=lambda p: isinstance(p, list),
            expected_type_name="list",
        )
        return result  # type: ignore[return-value]

    def request_json(
        self, path: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute API request expecting dict response with retry logic.

        Args:
            path: API endpoint path
            params: Optional query parameters

        Returns:
            JSON object as dictionary

        Raises:
            AuthenticationError: If authentication fails
            ApiError: If request fails after retries
        """
        result = self._execute_with_retry(
            path=path,
            params=params,
            validator=lambda p: isinstance(p, dict),
            expected_type_name="dict",
        )
        return result  # type: ignore[return-value]

    def request_all(
        self, path: str, params: Optional[Dict[str, Any]] = None, max_pages: int = 100
    ) -> List[Dict[str, Any]]:
        """Retrieve all pages for a list-based GitHub API endpoint.

        Args:
            path: API endpoint path
            params: Optional query parameters
            max_pages: Maximum number of pages to fetch (default: 100, prevents infinite loops)

        Returns:
            All items from all pages (up to max_pages)
        """
        base_params: Dict[str, Any] = dict(params or {})
        per_page = int(base_params.get("per_page") or 100)
        return self.paginate(path, base_params, per_page=per_page, max_pages=max_pages)

    def paginate(
        self,
        path: str,
        base_params: Dict[str, Any],
        per_page: int = 100,
        early_stop: Optional[Callable[[Dict[str, Any]], bool]] = None,
        max_pages: int = 100,
    ) -> List[Dict[str, Any]]:
        """Generic pagination helper with optional early stopping.

        Args:
            path: API endpoint path
            base_params: Base query parameters
            per_page: Items per page (default: 100)
            early_stop: Optional callback that receives each item and returns True to stop
            max_pages: Maximum number of pages to fetch (default: 100, prevents infinite loops)

        Returns:
            List of collected items (up to max_pages)

        Raises:
            ValueError: If per_page or max_pages is not positive
        """
        if per_page <= 0:
            raise ValueError(f"per_page must be positive, got {per_page}")
        if max_pages <= 0:
            raise ValueError(f"max_pages must be positive, got {max_pages}")

        results: List[Dict[str, Any]] = []
        page = 1

        while page <= max_pages:
            page_params = base_params | {"page": page, "per_page": per_page}
            data = self.request_list(path, page_params)

            if not data:
                break

            # Check early stop condition for each item
            if early_stop:
                for item in data:
                    if early_stop(item):
                        return results
                    results.append(item)
            else:
                results.extend(data)

            if len(data) < per_page:
                break

            page += 1

        return results

    def close(self) -> None:
        """Close the requests session and release resources."""
        if self.session is not None:
            self.session.close()
            self.session = None

    def __enter__(self) -> "GitHubApiClient":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit - close session."""
        self.close()
