"""Generate demo data for a realistic-looking system."""
import random
import uuid
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.constants import ModelProvider, ModelStatus, UserRole, UserStatus
from app.core.security import generate_api_key, get_password_hash
from app.db.clickhouse import insert_audit_log, insert_risk_event
from app.db.mysql import AsyncSessionLocal
from app.models import User, UserQuota
from app.models.ai_model import AIModel
from app.models.audit import UsageLog


# Demo constants
FIRST_NAMES = ["李", "王", "张", "刘", "陈", "杨", "赵", "黄", "周", "吴", "徐", "孙", "胡", "朱", "高"]
LAST_NAMES = ["伟", "芳", "娜", "敏", "静", "丽", "强", "磊", "军", "洋", "勇", "艳", "杰", "娟", "涛"]
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15",
]
REQUEST_PATHS = ["/v1/chat/completions", "/api/v1/models", "/api/v1/admin/stats"]
MODEL_NAMES = ["gpt-4", "gpt-3.5-turbo", "claude-3-opus", "azure-gpt-4"]
RISK_REASONS = [
    "非工作时间大量调用 API",
    "检测到敏感信息查询",
    "短时间内请求频率异常",
    "IP 地址存在异常",
    "提示词注入攻击尝试",
]
RISK_DESCRIPTIONS = [
    "用户在凌晨 3 点发起大量请求",
    "查询内容包含密码相关关键词",
    "1 分钟内请求超过 120 次",
    "来自非常用 IP 的访问",
    "检测到 ignore previous instructions 注入模式",
]


def _random_name() -> str:
    return random.choice(FIRST_NAMES) + random.choice(LAST_NAMES)


def _random_ip() -> str:
    return f"{random.randint(1, 223)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}"


def _random_time_in_last_days(days: int = 30) -> datetime:
    return datetime.utcnow() - timedelta(
        days=random.randint(0, days),
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59),
        seconds=random.randint(0, 59),
    )


async def _seed_models(session) -> list[AIModel]:
    """Seed demo AI models."""
    result = await session.execute(select(AIModel))
    if result.scalars().first():
        return []

    models_data = [
        {
            "name": "GPT-4",
            "model_id": "gpt-4",
            "provider": ModelProvider.OPENAI,
            "base_url": "https://api.openai.com/v1",
            "api_key": "sk-demo-openai-" + uuid.uuid4().hex[:16],
            "status": ModelStatus.ACTIVE,
            "is_default": True,
            "temperature": 0.7,
            "max_tokens": 4096,
        },
        {
            "name": "GPT-3.5 Turbo",
            "model_id": "gpt-3.5-turbo",
            "provider": ModelProvider.OPENAI,
            "base_url": "https://api.openai.com/v1",
            "api_key": "sk-demo-openai-" + uuid.uuid4().hex[:16],
            "status": ModelStatus.ACTIVE,
            "is_default": False,
            "temperature": 0.8,
            "max_tokens": 2048,
        },
        {
            "name": "Claude 3 Opus",
            "model_id": "claude-3-opus-20240229",
            "provider": ModelProvider.ANTHROPIC,
            "base_url": "https://api.anthropic.com/v1",
            "api_key": "sk-demo-anthropic-" + uuid.uuid4().hex[:16],
            "status": ModelStatus.ACTIVE,
            "is_default": False,
            "temperature": 0.6,
            "max_tokens": 4096,
        },
        {
            "name": "Azure GPT-4",
            "model_id": "gpt-4",
            "provider": ModelProvider.AZURE,
            "base_url": "https://my-resource.openai.azure.com/",
            "api_key": "sk-demo-azure-" + uuid.uuid4().hex[:16],
            "status": ModelStatus.INACTIVE,
            "is_default": False,
            "temperature": 0.7,
            "max_tokens": 4096,
        },
    ]

    models = []
    for data in models_data:
        model = AIModel(**data)
        session.add(model)
        models.append(model)
    await session.flush()
    return models


async def _seed_demo_users(session) -> list[User]:
    """Seed demo regular users."""
    users = []
    for i in range(10):
        username = f"user{i+1:02d}"
        email = f"{username}@example.com"
        result = await session.execute(select(User).where(User.username == username))
        if result.scalar_one_or_none():
            continue

        user = User(
            uuid=str(uuid.uuid4()),
            username=username,
            email=email,
            password=get_password_hash("password123"),
            role=UserRole.USER,
            status=random.choice([UserStatus.ACTIVE, UserStatus.ACTIVE, UserStatus.ACTIVE, UserStatus.INACTIVE]),
            api_key=generate_api_key(),
        )
        session.add(user)
        await session.flush()

        quota = UserQuota(
            user_id=user.id,
            daily_limit=random.choice([50000, 100000, 200000]),
            weekly_limit=random.choice([200000, 500000, 1000000]),
            monthly_limit=random.choice([1000000, 2000000, 5000000]),
        )
        session.add(quota)
        users.append(user)

    await session.flush()
    return users


async def _seed_usage_logs(session, users: list[User], models: list[AIModel]) -> None:
    """Seed MySQL usage_logs."""
    result = await session.execute(select(UsageLog))
    if result.scalars().first():
        return

    logs = []
    for user in users:
        if user.status != UserStatus.ACTIVE:
            continue
        for _ in range(random.randint(30, 80)):
            req_time = _random_time_in_last_days(30)
            latency = random.randint(200, 3000)
            resp_time = req_time + timedelta(milliseconds=latency)
            prompt_tokens = random.randint(50, 2000)
            completion_tokens = random.randint(20, 1500)

            log = UsageLog(
                user_id=user.id,
                request_id=str(uuid.uuid4()),
                model_name=random.choice(MODEL_NAMES),
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
                request_time=req_time,
                response_time=resp_time,
                latency_ms=latency,
                status=random.choices(["success", "success", "success", "error"], weights=[70, 10, 10, 10])[0],
                error_message=random.choice([None, None, None, "Rate limit exceeded", "Model timeout"]),
                ip=_random_ip(),
                user_agent=random.choice(USER_AGENTS),
            )
            logs.append(log)

    # Admin usage
    admin_result = await session.execute(select(User).where(User.username == "admin"))
    admin = admin_result.scalar_one_or_none()
    if admin:
        for _ in range(50):
            req_time = _random_time_in_last_days(30)
            latency = random.randint(150, 2500)
            resp_time = req_time + timedelta(milliseconds=latency)
            prompt_tokens = random.randint(100, 3000)
            completion_tokens = random.randint(50, 2000)
            logs.append(UsageLog(
                user_id=admin.id,
                request_id=str(uuid.uuid4()),
                model_name=random.choice(MODEL_NAMES),
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
                request_time=req_time,
                response_time=resp_time,
                latency_ms=latency,
                status="success",
                ip=_random_ip(),
                user_agent=random.choice(USER_AGENTS),
            ))

    for log in logs:
        session.add(log)
    await session.flush()


async def _update_quota_usage(session, users: list[User]) -> None:
    """Update quota usage based on usage_logs."""
    from sqlalchemy import func

    for user in users:
        result = await session.execute(
            select(
                func.coalesce(func.sum(UsageLog.total_tokens), 0),
                func.count(UsageLog.id),
            ).where(
                UsageLog.user_id == user.id,
                UsageLog.request_time >= datetime.utcnow() - timedelta(days=1)
            )
        )
        daily_tokens, daily_count = result.one()

        result = await session.execute(
            select(
                func.coalesce(func.sum(UsageLog.total_tokens), 0),
            ).where(
                UsageLog.user_id == user.id,
                UsageLog.request_time >= datetime.utcnow() - timedelta(days=7)
            )
        )
        weekly_tokens = result.scalar_one()

        result = await session.execute(
            select(
                func.coalesce(func.sum(UsageLog.total_tokens), 0),
            ).where(
                UsageLog.user_id == user.id,
                UsageLog.request_time >= datetime.utcnow() - timedelta(days=30)
            )
        )
        monthly_tokens = result.scalar_one()

        quota_result = await session.execute(select(UserQuota).where(UserQuota.user_id == user.id))
        quota = quota_result.scalar_one_or_none()
        if quota:
            quota.daily_used = int(daily_tokens)
            quota.weekly_used = int(weekly_tokens)
            quota.monthly_used = int(monthly_tokens)

    await session.flush()


def _seed_clickhouse_audit_logs(users: list[User]) -> None:
    """Seed ClickHouse audit_logs."""
    # Generate ~800 audit logs
    for user in users:
        if user.status != UserStatus.ACTIVE:
            continue
        count = random.randint(50, 120)
        for _ in range(count):
            req_time = _random_time_in_last_days(30)
            latency = random.randint(200, 3000)
            resp_time = req_time + timedelta(milliseconds=latency)
            prompt_tokens = random.randint(50, 2000)
            completion_tokens = random.randint(20, 1500)
            total = prompt_tokens + completion_tokens
            has_error = random.random() < 0.1
            status_code = 500 if has_error else random.choice([200, 200, 200, 429])

            insert_audit_log({
                "timestamp": req_time,
                "request_id": str(uuid.uuid4()),
                "user_id": user.id,
                "user_name": user.username,
                "user_email": user.email,
                "request_time": req_time,
                "request_method": "POST",
                "request_path": "/v1/chat/completions",
                "request_ip": _random_ip(),
                "user_agent": random.choice(USER_AGENTS),
                "request_headers": "{\"Content-Type\": \"application/json\"}",
                "request_body": "{\"model\": \"gpt-4\", \"messages\": [...]}",
                "model_name": random.choice(MODEL_NAMES),
                "model_provider": random.choice(["openai", "anthropic", "azure"]),
                "response_time": resp_time,
                "response_status": status_code,
                "response_body": "{\"choices\": [...]}" if not has_error else "{\"error\": \"timeout\"}",
                "response_headers": "{}",
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total,
                "latency_ms": latency,
                "is_stream": random.random() < 0.3,
                "has_error": has_error,
                "error_message": "timeout" if has_error else "",
            })

    # Admin logs
    admin_user = next((u for u in users if u.username == "admin"), None)
    if admin_user:
        for _ in range(80):
            req_time = _random_time_in_last_days(30)
            latency = random.randint(100, 2000)
            resp_time = req_time + timedelta(milliseconds=latency)
            insert_audit_log({
                "timestamp": req_time,
                "request_id": str(uuid.uuid4()),
                "user_id": admin_user.id,
                "user_name": admin_user.username,
                "user_email": admin_user.email,
                "request_time": req_time,
                "request_method": random.choice(["GET", "GET", "POST"]),
                "request_path": random.choice(REQUEST_PATHS),
                "request_ip": _random_ip(),
                "user_agent": random.choice(USER_AGENTS),
                "request_headers": "{}",
                "request_body": "",
                "model_name": random.choice(MODEL_NAMES),
                "model_provider": "openai",
                "response_time": resp_time,
                "response_status": 200,
                "response_body": "{}",
                "response_headers": "{}",
                "prompt_tokens": random.randint(0, 500),
                "completion_tokens": random.randint(0, 300),
                "total_tokens": random.randint(0, 800),
                "latency_ms": latency,
                "is_stream": False,
                "has_error": False,
                "error_message": "",
            })


def _seed_clickhouse_risk_events(users: list[User]) -> None:
    """Seed ClickHouse risk_events."""
    risk_levels = ["low", "medium", "high", "critical"]
    risk_types = ["token_abuse", "off_hours_access", "sensitive_info", "abnormal_frequency", "ip_anomaly", "abnormal_pattern"]

    active_users = [u for u in users if u.status == UserStatus.ACTIVE]
    for _ in range(35):
        user = random.choice(active_users)
        idx = random.randint(0, len(RISK_REASONS) - 1)
        level = random.choices(risk_levels, weights=[30, 30, 25, 15])[0]
        resolved = random.random() < 0.4 if level in ["low", "medium"] else False
        timestamp = _random_time_in_last_days(14)

        insert_risk_event({
            "timestamp": timestamp,
            "event_id": str(uuid.uuid4()),
            "request_id": str(uuid.uuid4()),
            "user_id": user.id,
            "user_name": user.username,
            "risk_level": level,
            "risk_type": random.choice(risk_types),
            "risk_score": round(random.uniform(0.3, 0.95), 2),
            "risk_reason": RISK_REASONS[idx],
            "description": RISK_DESCRIPTIONS[idx],
            "evidence": "{\"requests\": 120, \"tokens\": 500000}",
            "request_ip": _random_ip(),
            "model_name": random.choice(MODEL_NAMES),
            "is_resolved": resolved,
            "resolved_by": "admin" if resolved else "",
            "resolved_at": timestamp + timedelta(hours=2) if resolved else datetime(1970, 1, 1),
            "note": "已处理" if resolved else "",
        })


async def seed_demo_data() -> None:
    """Main entry to seed all demo data."""
    async with AsyncSessionLocal() as session:
        # 1. Seed models
        models = await _seed_models(session)

        # 2. Seed users
        users = await _seed_demo_users(session)

        # 3. Fetch admin user
        admin_result = await session.execute(
            select(User).options(selectinload(User.quota)).where(User.username == "admin")
        )
        admin = admin_result.scalar_one_or_none()
        if admin:
            users.append(admin)

        if not users:
            return

        # Commit MySQL inserts so far
        await session.commit()

        # 4. Seed usage logs
        await _seed_usage_logs(session, users, models)
        await session.commit()

        # 5. Update quota usage
        await _update_quota_usage(session, users)
        await session.commit()

    # 6. Seed ClickHouse data (synchronous)
    _seed_clickhouse_audit_logs(users)
    _seed_clickhouse_risk_events(users)
