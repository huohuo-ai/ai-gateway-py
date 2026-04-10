"""Authentication middleware."""
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import UserRole, UserStatus
from app.core.security import decode_access_token
from app.db import get_db
from app.db.redis import get_cached_user, get_cached_user_by_api_key
from app.models import User
from app.services.user_service import UserService

security = HTTPBearer(auto_error=False)


async def verify_jwt_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """Verify JWT token and return payload."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header is required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if credentials.scheme != "Bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization scheme",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    payload = decode_access_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return payload


async def get_current_user(
    request: Request,
    token_payload: dict = Depends(verify_jwt_token),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get current user from JWT token."""
    user_id = int(token_payload.get("sub", 0))
    
    # Try cache first
    cached = await get_cached_user(user_id)
    
    service = UserService(db)
    user = await service.get_by_id(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if user.status != UserStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is not active"
        )
    
    # Store in request state for later use
    request.state.user = user
    request.state.user_id = user.id
    request.state.username = user.username
    
    return user


async def require_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """Require admin role."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permission required"
        )
    return current_user


async def verify_api_key(request: Request, db: AsyncSession = Depends(get_db)) -> User:
    """Verify API key authentication."""
    # Try X-API-Key header first
    api_key = request.headers.get("X-API-Key")
    
    # Fall back to Authorization: Bearer
    if not api_key:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            api_key = auth_header[7:]
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key is required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Try cache first
    cached = await get_cached_user_by_api_key(api_key)
    
    service = UserService(db)
    user = await service.get_by_api_key(api_key)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if user.status != UserStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is not active"
        )
    
    # Store in request state
    request.state.user = user
    request.state.user_id = user.id
    request.state.username = user.username
    request.state.api_key = api_key
    
    return user
