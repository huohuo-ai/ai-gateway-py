"""Audit and usage log models."""
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class UsageLog(Base):
    """Usage log for real-time statistics (MySQL)."""
    __tablename__ = "usage_logs"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        index=True
    )
    request_id: Mapped[str] = mapped_column(String(36), index=True)
    model_name: Mapped[str] = mapped_column(String(50), index=True)
    
    # Token usage
    prompt_tokens: Mapped[int] = mapped_column(BigInteger, default=0)
    completion_tokens: Mapped[int] = mapped_column(BigInteger, default=0)
    total_tokens: Mapped[int] = mapped_column(BigInteger, default=0)
    
    # Timing
    request_time: Mapped[datetime] = mapped_column(DateTime)
    response_time: Mapped[datetime] = mapped_column(DateTime)
    latency_ms: Mapped[int] = mapped_column(BigInteger)
    
    # Status
    status: Mapped[str] = mapped_column(String(20), default="success")
    error_message: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Client info
    ip: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="usage_logs")
    
    def __repr__(self) -> str:
        return f"<UsageLog {self.request_id}>"


# ClickHouse models (for reference, actual schema in SQL)
# These are used for type hints and documentation

class AuditLog:
    """Audit log model for ClickHouse.
    
    This is a Pydantic-like class for type hints.
    Actual table is created via SQL in ClickHouse.
    """
    timestamp: datetime
    request_id: str
    user_id: int
    user_name: str
    user_email: str
    request_time: datetime
    request_method: str
    request_path: str
    request_ip: str
    user_agent: str
    request_headers: str
    request_body: str
    model_name: str
    model_provider: str
    response_time: datetime
    response_status: int
    response_body: str
    response_headers: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    latency_ms: int
    is_stream: bool
    has_error: bool
    error_message: str


class RiskEvent:
    """Risk event model for ClickHouse."""
    timestamp: datetime
    event_id: str
    request_id: str
    user_id: int
    user_name: str
    risk_level: str  # low/medium/high/critical
    risk_type: str
    risk_score: float
    risk_reason: str
    description: str
    evidence: str  # JSON
    request_ip: str
    model_name: str
    is_resolved: bool
    resolved_by: Optional[str]
    resolved_at: Optional[datetime]
    note: Optional[str]
