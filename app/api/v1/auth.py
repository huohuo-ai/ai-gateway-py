"""Authentication routes."""
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.exceptions import UserAlreadyExistsError
from app.core.security import create_access_token, verify_password
from app.db import get_db
from app.middleware.auth import get_current_user
from app.schemas import (
    ChangePasswordRequest,
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    UserResponse,
)
from app.services.user_service import UserService

router = APIRouter()


@router.post("/login", response_model=LoginResponse)
async def login(
    request: Request,
    data: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """User login with username and password."""
    service = UserService(db)
    
    # Authenticate
    user = await service.authenticate(data.username, data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    # Update last login
    await service.update_last_login(user.id)
    
    # Create JWT token
    token = create_access_token(
        user_id=user.id,
        username=user.username,
        email=user.email,
        role=user.role
    )
    
    return LoginResponse(token=token, user=UserResponse.model_validate(user))


@router.post("/register", response_model=LoginResponse)
async def register(
    request: Request,
    data: RegisterRequest,
    db: AsyncSession = Depends(get_db)
):
    """User registration."""
    service = UserService(db)
    
    try:
        from app.core.constants import UserRole
        from app.schemas import UserCreate
        
        user_data = UserCreate(
            username=data.username,
            email=data.email,
            password=data.password,
            role=UserRole.USER
        )
        user = await service.create(user_data)
    except UserAlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    # Create JWT token
    token = create_access_token(
        user_id=user.id,
        username=user.username,
        email=user.email,
        role=user.role
    )
    
    return LoginResponse(token=token, user=UserResponse.model_validate(user))


@router.get("/profile", response_model=UserResponse)
async def get_profile(
    current_user = Depends(get_current_user)
):
    """Get current user profile."""
    return UserResponse.model_validate(current_user)


@router.post("/change-password")
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


@router.post("/regenerate-apikey")
async def regenerate_api_key(
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Regenerate API key."""
    service = UserService(db)
    new_key = await service.regenerate_api_key(current_user.id)
    
    return {"api_key": new_key}
