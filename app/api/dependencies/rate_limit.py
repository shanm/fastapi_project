from collections.abc import Callable

from fastapi import Depends, HTTPException, Request, status
from redis.asyncio import Redis

from app.core.redis import get_redis


def rate_limit(limit: int, window_seconds: int, key_prefix: str) -> Callable:
    async def dependency(
        request: Request,
        redis: Redis = Depends(get_redis),
    ) -> None:
        client_ip = request.client.host if request.client else "unknown"
        key = f"rate:{key_prefix}:{client_ip}"
        count = await redis.incr(key)
        if count == 1:
            await redis.expire(key, window_seconds)
        if count > limit:
            ttl = await redis.ttl(key)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests. Please try again later.",
                headers={"Retry-After": str(max(ttl, 1))},
            )

    return dependency


def login_rate_limit() -> Callable:
    async def dependency(
        request: Request,
        redis: Redis = Depends(get_redis),
    ) -> None:
        client_ip = request.client.host if request.client else "unknown"
        try:
            form = await request.form()
            username = form.get("username") or "unknown"
        except Exception:
            username = "unknown"
        key = f"rate:login:{client_ip}:{username.strip().lower()}"
        count = await redis.incr(key)
        if count == 1:
            await redis.expire(key, 60)
        if count > 5:
            ttl = await redis.ttl(key)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many login attempts. Please try again later.",
                headers={"Retry-After": str(max(ttl, 1))},
            )

    return dependency
