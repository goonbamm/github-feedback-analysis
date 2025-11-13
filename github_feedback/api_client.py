"""GitHub API client with Repository pattern."""

from __future__ import annotations

import logging
import time
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union

import requests

from .config import Config
from .constants import HTTP_STATUS, RETRY_CONFIG
from .exceptions import ApiError, AuthenticationError, ConfigurationError

logger = logging.getLogger(__name__)

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

    def __init__(self, config: Config, session: Optional[requests.Session] = None):
        """Initialize GitHub API client.

        Args:
            config: Configuration object with PAT and API URL
            session: Optional requests session for connection pooling

        Raises:
            ConfigurationError: If PAT is not configured
        """
        self.config = config
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
        """Get or create requests session.

        Returns:
            Configured requests session
        """
        if self.session is None:
            self.session = requests.Session()
            self.session.headers.update(self._headers)
        return self.session

    def _build_api_url(self, path: str) -> str:
        """Build full API URL from path.

        Args:
            path: API endpoint path

        Returns:
            Full API URL
        """
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

    def _should_retry(self, exc: Exception) -> bool:
        """Determine if request should be retried based on exception.

        Args:
            exc: Exception that occurred

        Returns:
            True if request should be retried
        """
        # Retry on network errors and rate limiting
        if isinstance(exc, requests.ConnectionError):
            return True
        if isinstance(exc, requests.Timeout):
            return True
        if isinstance(exc, requests.HTTPError):
            if exc.response is not None:
                # Retry on rate limiting and server errors
                return exc.response.status_code in HTTP_STATUS['retryable_errors']
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
                payload = response.json()

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
        self, path: str, params: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve all pages for a list-based GitHub API endpoint.

        Args:
            path: API endpoint path
            params: Optional query parameters

        Returns:
            All items from all pages
        """
        base_params: Dict[str, Any] = dict(params or {})
        per_page = int(base_params.get("per_page") or 100)
        return self.paginate(path, base_params, per_page=per_page)

    def paginate(
        self,
        path: str,
        base_params: Dict[str, Any],
        per_page: int = 100,
        early_stop: Optional[Callable[[Dict[str, Any]], bool]] = None,
    ) -> List[Dict[str, Any]]:
        """Generic pagination helper with optional early stopping.

        Args:
            path: API endpoint path
            base_params: Base query parameters
            per_page: Items per page (default: 100)
            early_stop: Optional callback that receives each item and returns True to stop

        Returns:
            List of collected items
        """
        results: List[Dict[str, Any]] = []
        page = 1

        while True:
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
