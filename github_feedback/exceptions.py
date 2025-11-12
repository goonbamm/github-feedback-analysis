"""Custom exceptions for GitHub Feedback Analysis."""


class GitHubFeedbackError(Exception):
    """Base exception for all GitHub feedback analysis errors."""

    pass


class AuthenticationError(GitHubFeedbackError):
    """Raised when GitHub authentication fails."""

    def __init__(self, message: str = "GitHub API authentication failed"):
        super().__init__(message)


class ConfigurationError(GitHubFeedbackError):
    """Raised when configuration is invalid or missing."""

    def __init__(self, message: str = "Invalid or missing configuration"):
        super().__init__(message)


class ApiError(GitHubFeedbackError):
    """Raised when GitHub API request fails."""

    def __init__(self, message: str, status_code: int | None = None):
        self.status_code = status_code
        super().__init__(f"{message} (status: {status_code})" if status_code else message)


class RateLimitError(ApiError):
    """Raised when GitHub API rate limit is exceeded."""

    def __init__(self, message: str = "GitHub API rate limit exceeded"):
        super().__init__(message, status_code=429)


class ResourceNotFoundError(ApiError):
    """Raised when a requested resource is not found."""

    def __init__(self, resource: str):
        super().__init__(f"Resource not found: {resource}", status_code=404)


class PermissionError(ApiError):
    """Raised when user lacks permission for requested operation."""

    def __init__(self, message: str = "Permission denied"):
        super().__init__(message, status_code=403)


class ValidationError(GitHubFeedbackError):
    """Raised when data validation fails."""

    def __init__(self, message: str):
        super().__init__(f"Validation error: {message}")


class CollectionError(GitHubFeedbackError):
    """Raised when data collection fails."""

    def __init__(self, message: str, cause: Exception | None = None):
        self.cause = cause
        full_message = f"Collection failed: {message}"
        if cause:
            full_message += f" (caused by: {cause})"
        super().__init__(full_message)
