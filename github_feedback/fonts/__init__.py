"""Helpers for accessing packaged font assets."""

from __future__ import annotations

import base64
import gzip
import tempfile
from pathlib import Path
from typing import Optional

from .hangul_font_data import FONT_BASE64

__all__ = ["ensure_hangul_font"]

_FONT_CACHE: Optional[Path] = None


def ensure_hangul_font() -> Path:
    """Return a filesystem path to the bundled Hangul-capable font.

    The font is stored as compressed base64 data to avoid committing large binary files.
    On first use it is extracted to a temporary location that persists for the duration
    of the process.
    """

    global _FONT_CACHE

    if _FONT_CACHE and _FONT_CACHE.exists():
        return _FONT_CACHE

    font_bytes = gzip.decompress(base64.b64decode(FONT_BASE64))
    with tempfile.NamedTemporaryFile(prefix="hangul_font_", suffix=".ttf", delete=False) as handle:
        handle.write(font_bytes)
        _FONT_CACHE = Path(handle.name)

    return _FONT_CACHE
