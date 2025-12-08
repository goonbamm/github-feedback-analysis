"""Backward compatibility module for analyzer.

This module maintains backward compatibility by re-exporting the refactored
Analyzer class from the new analyzer package.

The original 1,665-line analyzer.py has been refactored into a modular structure:
- analyzer/__init__.py: Main Analyzer orchestrator (~200 lines)
- analyzer/helpers/: Helper classes (ActivityMessageBuilder, InsightExtractor, etc.)
- analyzer/builders/: Metric builders (HighlightsBuilder, SummaryBuilder, etc.)
- analyzer/witch_critique/: Witch critique generation with checks
- analyzer/trends/: Trend analysis components
- analyzer/year_end/: Year-end review builder

For new code, prefer importing directly from github_feedback.analyzer
"""

# Re-export everything from the refactored analyzer module
from github_feedback.analyzer import Analyzer

# Re-export helper classes for backward compatibility
from github_feedback.analyzer.helpers import (
    ActivityMessageBuilder,
    InsightExtractor,
    PeriodFormatter,
)

__all__ = [
    "Analyzer",
    "ActivityMessageBuilder",
    "InsightExtractor",
    "PeriodFormatter",
]
