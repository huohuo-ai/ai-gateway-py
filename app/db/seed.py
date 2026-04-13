"""Database seeding with default data."""
from uuid import uuid4

from sqlalchemy import select

from app.core.constants import PatternType, RiskLevel, UserRole, UserStatus
from app.db.mysql import AsyncSessionLocal
from app.models.prompt_pattern import PromptPattern
from app.models.user import User, UserQuota


async def seed_database() -> None:
    """Seed database with default admin user and prompt patterns."""
    async with AsyncSessionLocal() as session:
        # Check if admin user exists
        result = await session.execute(select(User).where(User.username == "admin"))
        admin = result.scalar_one_or_none()

        if admin is None:
            admin_uuid = str(uuid4())
            api_key = f"ak-{uuid4().hex.lower()}"
            admin = User(
                uuid=admin_uuid,
                username="admin",
                email="admin@example.com",
                password="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewKyNiAYMyzJ/I3K",
                role=UserRole.ADMIN,
                status=UserStatus.ACTIVE,
                api_key=api_key,
            )
            session.add(admin)
            await session.flush()  # Get admin.id

            # Create quota for admin
            quota = UserQuota(
                user_id=admin.id,
                daily_limit=1_000_000,
                weekly_limit=5_000_000,
                monthly_limit=20_000_000,
            )
            session.add(quota)

        # Seed default prompt patterns
        default_patterns = [
            {
                "pattern": "password|密码",
                "pattern_type": PatternType.SENSITIVE_INFO,
                "risk_level": RiskLevel.MEDIUM,
                "description": "密码相关查询",
            },
            {
                "pattern": "secret|密钥|secret",
                "pattern_type": PatternType.SENSITIVE_INFO,
                "risk_level": RiskLevel.HIGH,
                "description": "密钥相关查询",
            },
            {
                "pattern": "salary|工资|薪资",
                "pattern_type": PatternType.SENSITIVE_INFO,
                "risk_level": RiskLevel.HIGH,
                "description": "薪资相关查询",
            },
            {
                "pattern": "ignore previous|忽略之前",
                "pattern_type": PatternType.INJECTION,
                "risk_level": RiskLevel.HIGH,
                "description": "提示词注入攻击",
            },
            {
                "pattern": "developer mode|开发者模式",
                "pattern_type": PatternType.INJECTION,
                "risk_level": RiskLevel.HIGH,
                "description": "开发者模式注入",
            },
            {
                "pattern": "DAN mode|DAN",
                "pattern_type": PatternType.INJECTION,
                "risk_level": RiskLevel.HIGH,
                "description": "DAN模式注入",
            },
            {
                "pattern": "system prompt|系统提示",
                "pattern_type": PatternType.INJECTION,
                "risk_level": RiskLevel.HIGH,
                "description": "系统提示提取",
            },
        ]

        for pattern_data in default_patterns:
            result = await session.execute(
                select(PromptPattern).where(
                    PromptPattern.pattern == pattern_data["pattern"]
                )
            )
            existing = result.scalar_one_or_none()
            if existing is None:
                session.add(PromptPattern(**pattern_data, is_enabled=True))

        await session.commit()
