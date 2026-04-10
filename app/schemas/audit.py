"""Audit and risk event schemas."""
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class AuditLogQuery(BaseModel):
    """Audit log query parameters."""
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    user_id: Optional[int] = None
    model_name: Optional[str] = None
    risk_level: Optional[str] = None
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)


class AuditLogResponse(BaseModel):
    """Audit log response."""
    model_config = ConfigDict(from_attributes=True)
    
    timestamp: datetime
    request_id: str
    user_id: int
    user_name: str
    user_email: str
    request_method: str
    request_path: str
    request_ip: str
    model_name: str
    response_status: int
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    latency_ms: int
    is_stream: bool
    has_error: bool
    error_message: str


class RiskEventResponse(BaseModel):
    """Risk event response."""
    model_config = ConfigDict(from_attributes=True)
    
    timestamp: datetime
    event_id: str
    request_id: str
    user_id: int
    user_name: str
    risk_level: str
    risk_type: str
    risk_score: float
    risk_reason: str
    description: str
    evidence: str
    request_ip: str
    model_name: str
    is_resolved: bool
    resolved_by: str
    resolved_at: Optional[datetime]
    note: str


class RiskEventResolveRequest(BaseModel):
    """Risk event resolve request."""
    note: Optional[str] = None


class UserStatistics(BaseModel):
    """User usage statistics."""
    date: str
    total_requests: int
    total_tokens: int
    prompt_tokens: int
    completion_tokens: int


class DashboardStats(BaseModel):
    """Dashboard statistics."""
    today_requests: int
    today_tokens: int
    active_users: int
    risk_events: int
    trends: list[dict[str, Any]]
    model_stats: list[dict[str, Any]]


class PaginatedResponse(BaseModel):
    """Paginated response wrapper."""
    data: list[Any]
    total: int
    page: int
    page_size: int
