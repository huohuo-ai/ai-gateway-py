"""Pydantic schemas for request/response validation."""
from app.schemas.user import (
    UserCreate,
    UserResponse,
    UserUpdate,
    UserQuotaResponse,
    UserQuotaUpdate,
)
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    ChangePasswordRequest,
)
from app.schemas.ai_model import (
    AIModelCreate,
    AIModelResponse,
    AIModelUpdate,
)
from app.schemas.llm import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatMessage,
    ModelListResponse,
    Usage,
)
from app.schemas.audit import (
    AuditLogQuery,
    AuditLogResponse,
    RiskEventResponse,
    DashboardStats,
)

__all__ = [
    # User
    "UserCreate",
    "UserResponse",
    "UserUpdate",
    "UserQuotaResponse",
    "UserQuotaUpdate",
    # Auth
    "LoginRequest",
    "LoginResponse",
    "RegisterRequest",
    "ChangePasswordRequest",
    # AI Model
    "AIModelCreate",
    "AIModelResponse",
    "AIModelUpdate",
    # LLM
    "ChatCompletionRequest",
    "ChatCompletionResponse",
    "ChatMessage",
    "ModelListResponse",
    "Usage",
    # Audit
    "AuditLogQuery",
    "AuditLogResponse",
    "RiskEventResponse",
    "DashboardStats",
]
