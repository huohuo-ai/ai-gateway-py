"""User management routes (admin only)."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import UserRole, UserStatus
from app.core.exceptions import UserAlreadyExistsError, UserNotFoundError
from app.db import get_db
from app.middleware.auth import require_admin
from app.schemas import (
    UserCreate,
    UserQuotaResponse,
    UserQuotaUpdate,
    UserResponse,
    UserUpdate,
)
from app.services.quota_service import QuotaService
from app.services.user_service import UserService

router = APIRouter()


@router.get("", response_model=dict)
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    role: Optional[UserRole] = None,
    status: Optional[UserStatus] = None,
    db: AsyncSession = Depends(get_db),
    _ = Depends(require_admin)
):
    """List all users (admin only)."""
    service = UserService(db)
    users, total = await service.list_users(page, page_size, role, status)
    
    return {
        "data": [UserResponse.model_validate(u) for u in users],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post("", response_model=UserResponse)
async def create_user(
    data: UserCreate,
    db: AsyncSession = Depends(get_db),
    _ = Depends(require_admin)
):
    """Create new user (admin only)."""
    service = UserService(db)
    
    try:
        user = await service.create(data)
    except UserAlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    return UserResponse.model_validate(user)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    _ = Depends(require_admin)
):
    """Get user by ID (admin only)."""
    service = UserService(db)
    user = await service.get_by_id(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse.model_validate(user)


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    _ = Depends(require_admin)
):
    """Update user (admin only)."""
    service = UserService(db)
    
    try:
        user = await service.update(user_id, data)
    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    except UserAlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    return UserResponse.model_validate(user)


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    _ = Depends(require_admin)
):
    """Delete user (admin only)."""
    service = UserService(db)
    
    try:
        await service.delete(user_id)
    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {"message": "User deleted successfully"}


@router.post("/{user_id}/reset-password")
async def reset_password(
    user_id: int,
    data: dict,
    db: AsyncSession = Depends(get_db),
    _ = Depends(require_admin)
):
    """Reset user password (admin only)."""
    service = UserService(db)
    new_password = data.get("new_password", "password123")
    
    try:
        await service.reset_password(user_id, new_password)
    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {"message": "Password reset successfully"}


@router.get("/{user_id}/quota", response_model=UserQuotaResponse)
async def get_user_quota(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    _ = Depends(require_admin)
):
    """Get user quota (admin only)."""
    service = QuotaService(db)
    quota = await service.get_quota(user_id)
    
    return UserQuotaResponse.model_validate(quota)


@router.put("/{user_id}/quota", response_model=UserQuotaResponse)
async def update_user_quota(
    user_id: int,
    data: UserQuotaUpdate,
    db: AsyncSession = Depends(get_db),
    _ = Depends(require_admin)
):
    """Update user quota (admin only)."""
    service = QuotaService(db)
    quota = await service.update_quota(
        user_id,
        daily_limit=data.daily_limit,
        weekly_limit=data.weekly_limit,
        monthly_limit=data.monthly_limit
    )
    
    return UserQuotaResponse.model_validate(quota)
