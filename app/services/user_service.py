"""User service."""
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import UserRole, UserStatus
from app.core.exceptions import UserAlreadyExistsError, UserNotFoundError
from app.core.security import get_password_hash, verify_password
from app.models import User, UserQuota
from app.schemas import UserCreate, UserUpdate, UserQuotaUpdate


class UserService:
    """User business service."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        result = await self.db.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()
    
    async def get_by_api_key(self, api_key: str) -> Optional[User]:
        """Get user by API key."""
        result = await self.db.execute(
            select(User).where(User.api_key == api_key)
        )
        return result.scalar_one_or_none()
    
    async def authenticate(self, username: str, password: str) -> Optional[User]:
        """Authenticate user by username and password."""
        user = await self.get_by_username(username)
        if not user:
            return None
        if not verify_password(password, user.password):
            return None
        return user
    
    async def create(self, data: UserCreate) -> User:
        """Create new user."""
        # Check if username exists
        if await self.get_by_username(data.username):
            raise UserAlreadyExistsError(f"Username '{data.username}' already exists")
        
        # Check if email exists
        if await self.get_by_email(data.email):
            raise UserAlreadyExistsError(f"Email '{data.email}' already exists")
        
        # Create user
        user = User(
            username=data.username,
            email=data.email,
            password=get_password_hash(data.password),
            role=data.role,
            status=UserStatus.ACTIVE,
        )
        self.db.add(user)
        await self.db.flush()  # Get user.id
        
        # Create default quota
        quota = UserQuota(user_id=user.id)
        self.db.add(quota)
        
        await self.db.commit()
        await self.db.refresh(user)
        return user
    
    async def update(self, user_id: int, data: UserUpdate) -> User:
        """Update user."""
        user = await self.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(f"User {user_id} not found")
        
        # Update fields
        if data.username is not None:
            existing = await self.get_by_username(data.username)
            if existing and existing.id != user_id:
                raise UserAlreadyExistsError(f"Username '{data.username}' already exists")
            user.username = data.username
        
        if data.email is not None:
            existing = await self.get_by_email(data.email)
            if existing and existing.id != user_id:
                raise UserAlreadyExistsError(f"Email '{data.email}' already exists")
            user.email = data.email
        
        if data.role is not None:
            user.role = data.role
        
        if data.status is not None:
            user.status = data.status
        
        await self.db.commit()
        await self.db.refresh(user)
        return user
    
    async def delete(self, user_id: int) -> None:
        """Delete user."""
        user = await self.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(f"User {user_id} not found")
        
        await self.db.delete(user)
        await self.db.commit()
    
    async def list_users(
        self,
        page: int = 1,
        page_size: int = 20,
        role: Optional[UserRole] = None,
        status: Optional[UserStatus] = None
    ) -> tuple[list[User], int]:
        """List users with pagination."""
        query = select(User)
        
        if role:
            query = query.where(User.role == role)
        if status:
            query = query.where(User.status == status)
        
        # Get total count
        count_result = await self.db.execute(
            select(User).with_only_columns(User.id)
        )
        total = len(count_result.all())
        
        # Get paginated results
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        users = result.scalars().all()
        
        return list(users), total
    
    async def change_password(
        self,
        user_id: int,
        old_password: str,
        new_password: str
    ) -> User:
        """Change user password."""
        user = await self.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(f"User {user_id} not found")
        
        if not verify_password(old_password, user.password):
            raise ValueError("Invalid old password")
        
        user.password = get_password_hash(new_password)
        await self.db.commit()
        await self.db.refresh(user)
        return user
    
    async def reset_password(self, user_id: int, new_password: str) -> User:
        """Reset user password (admin only)."""
        user = await self.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(f"User {user_id} not found")
        
        user.password = get_password_hash(new_password)
        await self.db.commit()
        await self.db.refresh(user)
        return user
    
    async def regenerate_api_key(self, user_id: int) -> str:
        """Regenerate API key."""
        from app.core.security import generate_api_key
        
        user = await self.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(f"User {user_id} not found")
        
        user.api_key = generate_api_key()
        await self.db.commit()
        await self.db.refresh(user)
        return user.api_key
    
    async def update_last_login(self, user_id: int) -> None:
        """Update last login time."""
        from datetime import datetime
        
        user = await self.get_by_id(user_id)
        if user:
            user.last_login = datetime.utcnow()
            await self.db.commit()
