from redis.asyncio import Redis

REFRESH_TOKEN_PREFIX = "auth:refresh:"
USER_REFRESH_SET_PREFIX = "auth:user-refresh:"


def refresh_token_key(jti: str) -> str:
    return f"{REFRESH_TOKEN_PREFIX}{jti}"


def user_refresh_set_key(user_id: str) -> str:
    return f"{USER_REFRESH_SET_PREFIX}{user_id}"


async def store_refresh_token(redis: Redis, jti: str, user_id: str, ttl_seconds: int) -> None:
    await redis.set(refresh_token_key(jti), user_id, ex=ttl_seconds)
    await redis.sadd(user_refresh_set_key(user_id), jti)
    await redis.expire(user_refresh_set_key(user_id), ttl_seconds)


async def get_refresh_token_user(redis: Redis, jti: str) -> str | None:
    return await redis.get(refresh_token_key(jti))


async def revoke_refresh_token(redis: Redis, jti: str) -> None:
    user_id = await redis.get(refresh_token_key(jti))
    await redis.delete(refresh_token_key(jti))
    if user_id:
        await redis.srem(user_refresh_set_key(user_id), jti)


async def revoke_all_refresh_tokens(redis: Redis, user_id: str) -> None:
    set_key = user_refresh_set_key(user_id)
    jtis = await redis.smembers(set_key)
    if jtis:
        await redis.delete(*(refresh_token_key(jti) for jti in jtis))
    await redis.delete(set_key)
