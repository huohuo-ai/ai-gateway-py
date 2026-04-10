"""User and UserQuota models."""
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    BigInteger,
    DateTime,
    Enum,
    ForeignKey,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import UserRole, UserStatus
from app.core.security import generate_api_key, generate_uuid
from app.models.base import Base


class User(Base):
    """User model."""
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    uuid: Mapped[str] = mapped_column(
        String(36),
        unique=True,
        index=True,
        default=generate_uuid
    )
    username: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True
    )
    email: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True
    )
    password: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole),
        default=UserRole.USER
    )
    status: Mapped[UserStatus] = mapped_column(
        Enum(UserStatus),
        default=UserStatus.ACTIVE
    )
    api_key: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        index=True,
        default=generate_api_key
    )
    last_login: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True
    )
    
    # Relationships
    quota: Mapped[Optional["UserQuota"]] = relationship(
        "UserQuota",
        back_populates="user",
        uselist=False,
        lazy="selectin"
    )
    usage_logs: Mapped[list["UsageLog"]] = relationship(
        "UsageLog",
        back_populates="user",
        lazy="selectin"
    )
    
    @property
    def is_admin(self) -> bool:
        """Check if user is admin."""
        return self.role == UserRole.ADMIN
    
    @property
    def is_active(self) -> bool:
        """Check if user is active."""
        return self.status == UserStatus.ACTIVE
    
    def __repr__(self) -> str:
        return f"<User {self.username}>"


class UserQuota(Base):
    """User quota model."""
    __tablename__ = "user_quotas"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        unique=True,
        index=True
    )
    
    # Limits (0 means unlimited)
    daily_limit: Mapped[int] = mapped_column(
        BigInteger,
        default=100000
    )
    weekly_limit: Mapped[int] = mapped_column(
        BigInteger,
        default=500000
    )
    monthly_limit: Mapped[int] = mapped_column(
        BigInteger,
        default=2000000
    )
    
    # Usage tracking
    daily_used: Mapped[int] = mapped_column(
        BigInteger,
        default=0
    )
    weekly_used: Mapped[int] = mapped_column(
        BigInteger,
        default=0
    )
    monthly_used: Mapped[int] = mapped_column(
        BigInteger,
        default=0
    )
    
    # Reset tracking
    last_reset_daily: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )
    last_reset_weekly: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )
    last_reset_monthly: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="quota")
    
    def check_quota(self, tokens: int) -> tuple[bool, str]:
        """Check if quota allows the request.
        
        Returns:
            Tuple of (allowed, reason)
        """
        # Check daily limit
        if self.daily_limit > 0 and self.daily_used + tokens > self.daily_limit:
            return False, "Daily quota exceeded"
        
        # Check weekly limit
        if self.weekly_limit > 0 and self.weekly_used + tokens > self.weekly_limit:
            return False, "Weekly quota exceeded"
        
        # Check monthly limit
        if self.monthly_limit > 0 and self.monthly_used + tokens > self.monthly_limit:
            return False, "Monthly quota exceeded"
        
        return True, ""
    
    def __repr__(self) -> str:
        return f"<UserQuota user_id={self.user_id}>"
