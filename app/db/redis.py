"""Redis connection."""
import redis.asyncio as aioredis

from app.config import settings

# Redis client instance
redis_client: aioredis.Redis | None = None


async def init_redis() -> aioredis.Redis:
    """Initialize Redis connection."""
    global redis_client
    redis_client = aioredis.Redis(
        host=settings.redis.host,
        port=settings.redis.port,
        db=settings.redis.db,
        password=settings.redis.password or None,
        decode_responses=settings.redis.decode_responses,
    )
    return redis_client


async def get_redis() -> aioredis.Redis:
    """Get Redis client."""
    if redis_client is None:
        await init_redis()
    return redis_client


async def close_redis() -> None:
    """Close Redis connection."""
    if redis_client:
        await redis_client.close()


# Cache helper functions

async def cache_user(user_id: int, user_data: dict, expire: int = 300) -> None:
    """Cache user by ID."""
    r = await get_redis()
    await r.setex(f"user:id:{user_id}", expire, str(user_data))


async def get_cached_user(user_id: int) -> dict | None:
    """Get cached user by ID."""
    r = await get_redis()
    data = await r.get(f"user:id:{user_id}")
    if data:
        import json
        return json.loads(data)
    return None


async def cache_user_by_api_key(api_key: str, user_data: dict, expire: int = 300) -> None:
    """Cache user by API key."""
    r = await get_redis()
    await r.setex(f"user:apikey:{api_key}", expire, str(user_data))


async def get_cached_user_by_api_key(api_key: str) -> dict | None:
    """Get cached user by API key."""
    r = await get_redis()
    data = await r.get(f"user:apikey:{api_key}")
    if data:
        import json
        return json.loads(data)
    return None


async def delete_user_cache(user_id: int, api_key: str) -> None:
    """Delete user cache."""
    r = await get_redis()
    pipe = r.pipeline()
    pipe.delete(f"user:id:{user_id}")
    pipe.delete(f"user:apikey:{api_key}")
    await pipe.execute()


async def check_rate_limit(key: str, limit: int, window: int = 60) -> tuple[bool, int]:
    """Check rate limit using sliding window.
    
    Returns:
        Tuple of (allowed, current_count)
    """
    r = await get_redis()
    current = await r.get(key)
    
    if current is None:
        await r.setex(key, window, 1)
        return True, 1
    
    count = int(current)
    if count >= limit:
        return False, count
    
    await r.incr(key)
    return True, count + 1
