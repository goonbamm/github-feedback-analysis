"""Custom exceptions for the GitHub feedback toolkit."""

from __future__ import annotations


class GHFError(Exception):
    """Base exception for all GitHub Feedback Analysis errors."""
    pass


# =============================================================================
# Configuration Errors
# =============================================================================


class ConfigurationError(GHFError):
    """Raised when there's a configuration problem."""
    pass




# =============================================================================
# Authentication Errors
# =============================================================================


class AuthenticationError(GHFError):
    """Raised when authentication fails."""
    pass




# =============================================================================
# Data Collection Errors
# =============================================================================


class CollectionError(GHFError):
    """Base exception for data collection errors."""

    def __init__(self, message: str, source: str | None = None):
        """Initialize collection error.

        Args:
            message: Error message
            source: Source of the error (e.g., 'commits', 'pull_requests')
        """
        super().__init__(message)
        self.source = source


class CollectionTimeoutError(CollectionError):
    """Raised when data collection times out."""
    pass




class ApiError(CollectionError):
    """Raised when GitHub API request fails."""

    def __init__(self, message: str, status_code: int | None = None):
        """Initialize API error.

        Args:
            message: Error message
            status_code: HTTP status code if available
        """
        super().__init__(message)
        self.status_code = status_code


class RateLimitError(ApiError):
    """Raised when GitHub API rate limit is exceeded."""
    pass


class RepositoryAccessError(ApiError):
    """Raised when unable to access repository (not found or no permission)."""
    pass


# =============================================================================
# Analysis Errors
# =============================================================================


class AnalysisError(GHFError):
    """Base exception for analysis errors."""
    pass


class InsufficientDataError(AnalysisError):
    """Raised when insufficient data is available for analysis."""
    pass


class MetricsCalculationError(AnalysisError):
    """Raised when metrics calculation fails."""
    pass


class LLMAnalysisError(AnalysisError):
    """Raised when LLM-based analysis fails."""

    def __init__(self, message: str, analysis_type: str | None = None):
        """Initialize LLM analysis error.

        Args:
            message: Error message
            analysis_type: Type of analysis that failed (e.g., 'commit_messages')
        """
        super().__init__(message)
        self.analysis_type = analysis_type


class LLMConnectionError(LLMAnalysisError):
    """Raised when connection to LLM server fails."""
    pass


class LLMTimeoutError(LLMAnalysisError):
    """Raised when LLM analysis times out."""
    pass


class LLMResponseError(LLMAnalysisError):
    """Raised when LLM returns an invalid or malformed response."""
    pass


class LLMValidationError(LLMAnalysisError):
    """Raised when LLM response fails schema validation."""
    pass


class LLMRateLimitError(LLMAnalysisError):
    """Raised when LLM rate limit is exceeded."""
    pass




# =============================================================================
# Report Generation Errors
# =============================================================================


class ReportGenerationError(GHFError):
    """Base exception for report generation errors."""
    pass




# =============================================================================
# Validation Errors
# =============================================================================


class ValidationError(GHFError):
    """Base exception for validation errors."""
    pass


class InvalidInputError(ValidationError):
    """Raised when user input is invalid."""
    pass


class InvalidPATError(ValidationError):
    """Raised when the GitHub Personal Access Token is invalid."""
    pass


class InvalidRepositoryError(ValidationError):
    """Raised when the repository format is invalid."""
    pass


class InvalidDateRangeError(ValidationError):
    """Raised when date range is invalid."""
    pass




