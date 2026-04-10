"""User schemas."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.core.constants import UserRole, UserStatus


class UserBase(BaseModel):
    """Base user schema."""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr


class UserCreate(UserBase):
    """User creation schema."""
    password: str = Field(..., min_length=6)
    role: UserRole = UserRole.USER


class UserUpdate(BaseModel):
    """User update schema."""
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    role: Optional[UserRole] = None
    status: Optional[UserStatus] = None


class UserQuotaResponse(BaseModel):
    """User quota response schema."""
    model_config = ConfigDict(from_attributes=True)
    
    daily_limit: int
    weekly_limit: int
    monthly_limit: int
    daily_used: int
    weekly_used: int
    monthly_used: int
    last_reset_daily: datetime
    last_reset_weekly: datetime
    last_reset_monthly: datetime


class UserQuotaUpdate(BaseModel):
    """User quota update schema."""
    daily_limit: Optional[int] = None
    weekly_limit: Optional[int] = None
    monthly_limit: Optional[int] = None


class UserResponse(BaseModel):
    """User response schema."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    uuid: str
    username: str
    email: str
    role: UserRole
    status: UserStatus
    api_key: str
    last_login: Optional[datetime] = None
    created_at: datetime
    quota: Optional[UserQuotaResponse] = None


class UserInDB(UserResponse):
    """User with password (internal use)."""
    password: str
