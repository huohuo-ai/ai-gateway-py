"""Security utilities for authentication and authorization."""
from datetime import datetime, timedelta
from typing import Any, Optional, Union
from uuid import uuid4

import bcrypt
import jwt
from ulid import ULID

from app.config import settings
from app.core.constants import API_KEY_PREFIX, UserRole


# Password hashing

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password."""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8")
    )


def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt."""
    return bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")


# JWT Token handling

def create_access_token(
    user_id: int,
    username: str,
    email: str,
    role: UserRole,
    expires_delta: Optional[timedelta] = None
) -> str:
    """Create a JWT access token."""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(seconds=settings.jwt.expires_in)

    to_encode = {
        "sub": str(user_id),
        "username": username,
        "email": email,
        "role": role.value,
        "exp": expire,
        "iat": datetime.utcnow(),
        "iss": "ai-gateway",
        "jti": str(uuid4()),
    }

    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt.secret,
        algorithm=settings.jwt.algorithm
    )
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict[str, Any]]:
    """Decode and validate a JWT access token."""
    try:
        payload = jwt.decode(
            token,
            settings.jwt.secret,
            algorithms=[settings.jwt.algorithm],
            issuer="ai-gateway"
        )
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
    except Exception:
        # Catch any other decoding errors (e.g. library version differences)
        return None


# API Key generation

def generate_api_key() -> str:
    """Generate a new API key."""
    return f"{API_KEY_PREFIX}{str(ULID()).lower()}"


def generate_uuid() -> str:
    """Generate a UUID string."""
    return str(uuid4())
