"""Christmas theme module for seasonal CLI decorations."""

from __future__ import annotations

from datetime import datetime


def is_christmas_season() -> bool:
    """Check if the current date is within the Christmas season (Nov 1 - Dec 31)."""
    now = datetime.now()
    return now.month in (11, 12)


def get_christmas_banner() -> str:
    """Return a festive Christmas banner."""
    return """
🎄 Happy Holidays! 🎄
"""
