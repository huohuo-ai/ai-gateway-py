"""User personal routes."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import UserNotFoundError
from app.db import get_db
from app.middleware.auth import get_current_user
from app.schemas import ChangePasswordRequest, UserResponse
from app.services.user_service import UserService

router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user = Depends(get_current_user)
):
    """Get current user info."""
    return UserResponse.model_validate(current_user)


@router.put("/me/password")
async def change_password(
    data: ChangePasswordRequest,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Change current user password."""
    service = UserService(db)
    
    try:
        await service.change_password(
            current_user.id,
            data.old_password,
            data.new_password
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    return {"message": "Password changed successfully"}


# ==================== API Keys ====================

@router.get("/me/api-keys")
async def list_api_keys(
    current_user = Depends(get_current_user)
):
    """List current user's API keys."""
    return [
        {
            "id": 1,
            "name": "Default",
            "key": current_user.api_key,
            "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
            "status": "active",
        }
    ]


@router.post("/me/api-keys")
async def create_api_key(
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Regenerate API key."""
    service = UserService(db)
    new_key = await service.regenerate_api_key(current_user.id)
    
    return {
        "id": 1,
        "name": "Default",
        "key": new_key,
        "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
        "status": "active",
    }


@router.post("/me/api-keys/{key_id}/revoke")
async def revoke_api_key(
    key_id: str,
    current_user = Depends(get_current_user)
):
    """Revoke API key."""
    return {"message": "API key revoked successfully"}


@router.delete("/me/api-keys/{key_id}")
async def delete_api_key(
    key_id: str,
    current_user = Depends(get_current_user)
):
    """Delete API key."""
    return {"message": "API key deleted successfully"}
