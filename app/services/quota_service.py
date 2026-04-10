"""Quota service."""
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.exceptions import QuotaExceededError
from app.models import UserQuota


class QuotaService:
    """Quota management service."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_quota(self, user_id: int) -> UserQuota:
        """Get or create user quota."""
        result = await self.db.execute(
            select(UserQuota).where(UserQuota.user_id == user_id)
        )
        quota = result.scalar_one_or_none()
        
        if not quota:
            # Create default quota
            quota = UserQuota(
                user_id=user_id,
                daily_limit=settings.default_quota.daily_limit,
                weekly_limit=settings.default_quota.weekly_limit,
                monthly_limit=settings.default_quota.monthly_limit,
            )
            self.db.add(quota)
            await self.db.commit()
            await self.db.refresh(quota)
        
        return quota
    
    async def update_quota(
        self,
        user_id: int,
        daily_limit: int = None,
        weekly_limit: int = None,
        monthly_limit: int = None
    ) -> UserQuota:
        """Update user quota limits."""
        quota = await self.get_quota(user_id)
        
        if daily_limit is not None:
            quota.daily_limit = daily_limit
        if weekly_limit is not None:
            quota.weekly_limit = weekly_limit
        if monthly_limit is not None:
            quota.monthly_limit = monthly_limit
        
        await self.db.commit()
        await self.db.refresh(quota)
        return quota
    
    async def check_and_reset_quota(self, user_id: int) -> UserQuota:
        """Check if quota needs reset and reset if necessary."""
        quota = await self.get_quota(user_id)
        now = datetime.utcnow()
        
        # Check daily reset
        if now - quota.last_reset_daily >= timedelta(days=1):
            quota.daily_used = 0
            quota.last_reset_daily = now
        
        # Check weekly reset
        if now - quota.last_reset_weekly >= timedelta(weeks=1):
            quota.weekly_used = 0
            quota.last_reset_weekly = now
        
        # Check monthly reset (30 days approximation)
        if now - quota.last_reset_monthly >= timedelta(days=30):
            quota.monthly_used = 0
            quota.last_reset_monthly = now
        
        await self.db.commit()
        return quota
    
    async def check_quota(self, user_id: int, tokens: int) -> tuple[bool, str]:
        """Check if user has enough quota.
        
        Returns:
            Tuple of (allowed, reason)
        """
        quota = await self.check_and_reset_quota(user_id)
        return quota.check_quota(tokens)
    
    async def consume_quota(self, user_id: int, tokens: int) -> None:
        """Consume quota for user."""
        quota = await self.get_quota(user_id)
        
        quota.daily_used += tokens
        quota.weekly_used += tokens
        quota.monthly_used += tokens
        
        await self.db.commit()
    
    async def estimate_tokens(self, messages: list[dict], max_tokens: int = 0) -> int:
        """Estimate token usage from messages.
        
        Rough estimate: characters / 4 + max_tokens
        """
        total_chars = 0
        for msg in messages:
            content = msg.get("content", "")
            total_chars += len(content)
        
        estimated = total_chars // 4
        if max_tokens > 0:
            estimated += max_tokens
        else:
            estimated += 2000  # Default output
        
        return estimated
    
    async def check_before_request(
        self,
        user_id: int,
        messages: list[dict],
        max_tokens: int = 0
    ) -> None:
        """Check quota before making LLM request."""
        estimated = await self.estimate_tokens(messages, max_tokens)
        allowed, reason = await self.check_quota(user_id, estimated)
        
        if not allowed:
            raise QuotaExceededError(reason)
    
    async def consume_after_request(self, user_id: int, total_tokens: int) -> None:
        """Consume actual quota after LLM request."""
        await self.consume_quota(user_id, total_tokens)
