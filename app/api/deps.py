"""API dependencies."""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.middleware.auth import get_current_user, require_admin, verify_api_key, verify_jwt_token
from app.models import User

# Common dependencies
DBDependency = Depends(get_db)
CurrentUser = Depends(get_current_user)
AdminRequired = Depends(require_admin)
JWTAuth = Depends(verify_jwt_token)
APIKeyAuth = Depends(verify_api_key)

__all__ = [
    "get_db",
    "get_current_user",
    "require_admin",
    "verify_jwt_token",
    "verify_api_key",
    "DBDependency",
    "CurrentUser",
    "AdminRequired",
    "JWTAuth",
    "APIKeyAuth",
]
