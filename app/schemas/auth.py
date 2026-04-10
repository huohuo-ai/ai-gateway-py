"""Authentication schemas."""
from pydantic import BaseModel, Field

from app.schemas.user import UserResponse


class LoginRequest(BaseModel):
    """Login request schema."""
    username: str
    password: str


class LoginResponse(BaseModel):
    """Login response schema."""
    token: str
    user: UserResponse


class RegisterRequest(BaseModel):
    """Register request schema."""
    username: str = Field(..., min_length=3, max_length=50)
    email: str
    password: str = Field(..., min_length=6)


class ChangePasswordRequest(BaseModel):
    """Change password request schema."""
    old_password: str
    new_password: str = Field(..., min_length=6)
