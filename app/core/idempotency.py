from collections.abc import Callable
from uuid import UUID

from fastapi import Depends, Header, HTTPException, Request, status
from redis.asyncio import Redis

from app.core.redis import get_redis


def require_idempotency_key(ttl_seconds: int = 86400) -> Callable:
    async def dependency(
        request: Request,
        idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
        redis: Redis = Depends(get_redis),
    ) -> None:
        if not idempotency_key or not idempotency_key.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Idempotency-Key header is required.",
            )

        value = idempotency_key.strip()
        if len(value) > 128:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Idempotency-Key is too long.",
            )

        # User-scoped keys prevent one authenticated user from colliding with
        # another user's key. Fall back to the client IP for unauthenticated
        # endpoints using this dependency.
        user_id = getattr(request.state, "user_id", None)
        owner = str(user_id) if isinstance(user_id, UUID) else (
            request.client.host if request.client else "unknown"
        )
        key = f"idempotency:v1:{owner}:{request.method}:{request.url.path}:{value}"

        created = await redis.set(key, "in-progress", nx=True, ex=ttl_seconds)
        if not created:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Request with this Idempotency-Key is already in progress or has been processed.",
            )

    return dependency
