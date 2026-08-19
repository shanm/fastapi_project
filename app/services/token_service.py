from redis.asyncio import Redis


REFRESH_TOKEN_PREFIX = "auth:refresh:"


def refresh_token_key(jti: str) -> str:
    return f"{REFRESH_TOKEN_PREFIX}{jti}"


async def store_refresh_token(
    redis: Redis,
    jti: str,
    user_id: str,
    ttl_seconds: int,
) -> None:
    await redis.set(
        refresh_token_key(jti),
        user_id,
        ex=ttl_seconds,
    )


async def get_refresh_token_user(
    redis: Redis,
    jti: str,
) -> str | None:
    return await redis.get(refresh_token_key(jti))


async def revoke_refresh_token(
    redis: Redis,
    jti: str,
) -> None:
    await redis.delete(refresh_token_key(jti))
