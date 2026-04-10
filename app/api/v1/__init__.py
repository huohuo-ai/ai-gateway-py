"""API v1 router."""
from fastapi import APIRouter

from app.api.v1 import auth, llm, users, admin

api_router = APIRouter(prefix="/api/v1")

# Public routes
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])

# Authenticated routes
api_router.include_router(llm.router, prefix="", tags=["llm"])
api_router.include_router(users.router, prefix="/users", tags=["users"])

# Admin routes
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])

__all__ = ["api_router"]
