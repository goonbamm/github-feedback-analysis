"""Type definitions and enums."""

from __future__ import annotations

from enum import Enum

# =============================================================================
# Task Types
# =============================================================================

class TaskType(str, Enum):
    """Types of parallel tasks for consistent error handling and messaging."""

    COLLECTION = "collection"
    ANALYSIS = "analysis"
