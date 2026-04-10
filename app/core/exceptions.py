"""Custom exceptions for the application."""


class AI GatewayException(Exception):
    """Base exception for AI Gateway."""
    pass


class AuthenticationError(AI GatewayException):
    """Authentication failed."""
    pass


class AuthorizationError(AI GatewayException):
    """Not authorized."""
    pass


class QuotaExceededError(AI GatewayException):
    """Quota exceeded."""
    def __init__(self, message: str = "Quota exceeded", quota_type: str = "daily"):
        self.quota_type = quota_type
        super().__init__(message)


class RateLimitError(AI GatewayException):
    """Rate limit exceeded."""
    pass


class ModelNotFoundError(AI GatewayException):
    """Model not found."""
    pass


class ModelError(AI GatewayException):
    """LLM model error."""
    pass


class ValidationError(AI GatewayException):
    """Validation error."""
    pass


class UserNotFoundError(AI GatewayException):
    """User not found."""
    pass


class UserAlreadyExistsError(AI GatewayException):
    """User already exists."""
    pass
