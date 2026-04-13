"""Custom exceptions for the application."""


class AIGatewayException(Exception):
    """Base exception for AI Gateway."""
    pass


class AuthenticationError(AIGatewayException):
    """Authentication failed."""
    pass


class AuthorizationError(AIGatewayException):
    """Not authorized."""
    pass


class QuotaExceededError(AIGatewayException):
    """Quota exceeded."""
    def __init__(self, message: str = "Quota exceeded", quota_type: str = "daily"):
        self.quota_type = quota_type
        super().__init__(message)


class RateLimitError(AIGatewayException):
    """Rate limit exceeded."""
    pass


class ModelNotFoundError(AIGatewayException):
    """Model not found."""
    pass


class ModelError(AIGatewayException):
    """LLM model error."""
    pass


class ValidationError(AIGatewayException):
    """Validation error."""
    pass


class UserNotFoundError(AIGatewayException):
    """User not found."""
    pass


class UserAlreadyExistsError(AIGatewayException):
    """User already exists."""
    pass
