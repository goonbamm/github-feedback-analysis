"""LLM response caching utilities."""

from __future__ import annotations

import hashlib
import json
import logging
import time
from pathlib import Path
from typing import Any

from ..core.constants import SECONDS_PER_DAY

logger = logging.getLogger(__name__)

# Cache settings
DEFAULT_CACHE_EXPIRE_DAYS = 7
LLM_CACHE_DIR = Path.home() / ".cache" / "github_feedback" / "llm_cache"


def get_cache_key(data: Any) -> str:
    """Generate a cache key from input data using SHA256 hash.

    Args:
        data: Input data to hash

    Returns:
        SHA256 hash of the JSON-serialized data
    """
    json_str = json.dumps(data, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(json_str.encode("utf-8")).hexdigest()


def get_cache_path(cache_key: str) -> Path:
    """Get the file path for a cache key.

    Args:
        cache_key: Cache key hash

    Returns:
        Path to cache file

    Raises:
        PermissionError: If cache directory creation fails due to permissions
        OSError: If cache directory creation fails for other reasons
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


def load_from_cache(cache_key: str, max_age_days: int = DEFAULT_CACHE_EXPIRE_DAYS) -> str | None:
    """Load cached LLM response if it exists and is not expired.

    Args:
        cache_key: Cache key hash
        max_age_days: Maximum age in days before cache expires

    Returns:
        Cached response string, or None if not found or expired
    """
    try:
        cache_path = get_cache_path(cache_key)
    except OSError:
        return None

    if not cache_path.exists():
        return None

    # Check cache age
    age_seconds = time.time() - cache_path.stat().st_mtime
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


def save_to_cache(cache_key: str, response: str) -> None:
    """Save LLM response to cache.

    Args:
        cache_key: Cache key hash
        response: LLM response to cache

    Note:
        Errors are logged but not raised to avoid disrupting the main workflow
    """
    try:
        cache_path = get_cache_path(cache_key)
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
