"""GitHub API client with Repository pattern."""

from __future__ import annotations

import logging
from typing import Any, Callable, Dict, List, Optional

import requests

from .config import Config
from .exceptions import ApiError, AuthenticationError, ConfigurationError

logger = logging.getLogger(__name__)


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

    def request_list(
        self, path: str, params: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Execute API request expecting list response.

        Args:
            path: API endpoint path
            params: Optional query parameters

        Returns:
            List of JSON objects

        Raises:
            AuthenticationError: If authentication fails
            ApiError: If request fails
        """
        try:
            response = self._get_session().get(
                self._build_api_url(path),
                params=params,
                timeout=self._get_timeout(),
            )

            if response.status_code == 401:
                raise AuthenticationError("GitHub API rejected the provided PAT")

            response.raise_for_status()
            payload = response.json()

            if not isinstance(payload, list):
                raise ApiError(
                    f"Expected list response from {path}, got {type(payload).__name__}"
                )

            return payload

        except requests.HTTPError as exc:
            status_code = exc.response.status_code if exc.response else None
            raise ApiError(f"API request failed: {path}", status_code) from exc
        except requests.RequestException as exc:
            raise ApiError(f"Network error for {path}: {exc}") from exc

    def request_json(
        self, path: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute API request expecting dict response.

        Args:
            path: API endpoint path
            params: Optional query parameters

        Returns:
            JSON object as dictionary

        Raises:
            AuthenticationError: If authentication fails
            ApiError: If request fails
        """
        try:
            response = self._get_session().get(
                self._build_api_url(path),
                params=params,
                timeout=self._get_timeout(),
            )

            if response.status_code == 401:
                raise AuthenticationError("GitHub API rejected the provided PAT")

            response.raise_for_status()
            payload = response.json()

            if not isinstance(payload, dict):
                raise ApiError(
                    f"Expected dict response from {path}, got {type(payload).__name__}"
                )

            return payload

        except requests.HTTPError as exc:
            status_code = exc.response.status_code if exc.response else None
            raise ApiError(f"API request failed: {path}", status_code) from exc
        except requests.RequestException as exc:
            raise ApiError(f"Network error for {path}: {exc}") from exc

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
        results: List[Dict[str, Any]] = []
        base_params: Dict[str, Any] = dict(params or {})
        per_page = int(base_params.get("per_page") or 100)
        page = 1

        while True:
            page_params = base_params | {"page": page, "per_page": per_page}
            data = self.request_list(path, page_params)
            if not data:
                break
            results.extend(data)
            if len(data) < per_page:
                break
            page += 1

        return results

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
