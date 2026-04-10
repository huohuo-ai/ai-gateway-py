"""Rate limiting middleware."""
from fastapi import HTTPException, Request, status

from app.config import settings
from app.db.redis import check_rate_limit


async def rate_limit_middleware(
    request: Request,
    limit: int = None
) -> None:
    """Rate limiting based on user ID or IP."""
    # Get identifier
    user_id = getattr(request.state, "user_id", None)
    if user_id:
        key = f"rate_limit:user:{user_id}"
    else:
        client_ip = request.client.host if request.client else "unknown"
        key = f"rate_limit:ip:{client_ip}"
    
    limit = limit or settings.rate_limit.requests_per_minute
    allowed, current = await check_rate_limit(key, limit, window=60)
    
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Limit: {limit} requests per minute.",
            headers={
                "X-RateLimit-Limit": str(limit),
                "X-RateLimit-Remaining": "0",
            }
        )


class RateLimitMiddleware:
    """Global rate limiting middleware."""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        # Create request object
        from fastapi import Request
        request = Request(scope, receive)
        
        # Skip rate limit for certain paths
        path = request.url.path
        if path in ["/health", "/api/v1/auth/login", "/api/v1/auth/register"]:
            await self.app(scope, receive, send)
            return
        
        # Check rate limit
        try:
            await rate_limit_middleware(request)
        except HTTPException as e:
            # Return error response
            await send({
                "type": "http.response.start",
                "status": e.status_code,
                "headers": [(b"content-type", b"application/json")],
            })
            import json
            await send({
                "type": "http.response.body",
                "body": json.dumps({"detail": e.detail}).encode(),
            })
            return
        
        await self.app(scope, receive, send)
