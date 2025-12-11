"""Aggregate pull request reviews into an integrated annual report.

이 모듈은 backward compatibility를 위해 유지됩니다.
실제 구현은 review_reports/ 패키지로 분리되었습니다.
"""

# Backward compatibility: Re-export from refactored modules
from .review_reports import (
    PersonalDevelopmentAnalyzer,
    ReviewDataLoader,
    ReviewReporter,
    ReviewStatsCalculator,
    StoredReview,
)

__all__ = [
    "ReviewReporter",
    "StoredReview",
    "ReviewDataLoader",
    "PersonalDevelopmentAnalyzer",
    "ReviewStatsCalculator",
]
