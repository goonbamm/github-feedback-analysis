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


class InvalidConfigurationError(ConfigurationError):
    """Raised when configuration validation fails."""
    pass


class MissingConfigurationError(ConfigurationError):
    """Raised when required configuration is missing."""
    pass


# =============================================================================
# Authentication Errors
# =============================================================================


class AuthenticationError(GHFError):
    """Raised when authentication fails."""
    pass


class InvalidPATError(AuthenticationError):
    """Raised when the GitHub Personal Access Token is invalid."""
    pass


class InsufficientPermissionsError(AuthenticationError):
    """Raised when the PAT lacks required permissions."""
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


class APIRateLimitError(CollectionError):
    """Raised when GitHub API rate limit is exceeded."""

    def __init__(self, message: str, reset_at: int | None = None):
        """Initialize rate limit error.

        Args:
            message: Error message
            reset_at: Unix timestamp when rate limit resets
        """
        super().__init__(message)
        self.reset_at = reset_at


class RepositoryNotFoundError(CollectionError):
    """Raised when the requested repository doesn't exist or is inaccessible."""
    pass


class RepositoryAccessDeniedError(CollectionError):
    """Raised when access to the repository is denied."""
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


# =============================================================================
# Analysis Errors
# =============================================================================


class AnalysisError(GHFError):
    """Base exception for analysis errors."""
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


class MetricsComputationError(AnalysisError):
    """Raised when metrics computation fails."""
    pass


# =============================================================================
# Report Generation Errors
# =============================================================================


class ReportGenerationError(GHFError):
    """Base exception for report generation errors."""
    pass


class MarkdownGenerationError(ReportGenerationError):
    """Raised when markdown report generation fails."""
    pass


# =============================================================================
# Validation Errors
# =============================================================================


class ValidationError(GHFError):
    """Base exception for validation errors."""
    pass


class InvalidRepositoryFormatError(ValidationError):
    """Raised when repository format is invalid."""
    pass


class InvalidURLError(ValidationError):
    """Raised when URL validation fails."""
    pass


class InvalidMonthsError(ValidationError):
    """Raised when months value is invalid."""
    pass


# =============================================================================
# Network Errors
# =============================================================================


class NetworkError(GHFError):
    """Base exception for network-related errors."""
    pass


class ConnectionError(NetworkError):
    """Raised when network connection fails."""
    pass


class RequestTimeoutError(NetworkError):
    """Raised when network request times out."""
    pass


# =============================================================================
# File System Errors
# =============================================================================


class FileSystemError(GHFError):
    """Base exception for file system errors."""
    pass


class OutputDirectoryError(FileSystemError):
    """Raised when output directory operations fail."""
    pass


class FileWriteError(FileSystemError):
    """Raised when file write operations fail."""
    pass


class FileReadError(FileSystemError):
    """Raised when file read operations fail."""
    pass
