# JWT and password hashing mechanisms
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID, uuid4

from jose import JWTError, jwt
from pwdlib import PasswordHash

from app.core.config import settings


password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    """
    Hash a plain-text password using the recommended
    password hashing algorithm from pwdlib.
    """
    return password_hash.hash(password)


def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:
    """
    Verify a plain-text password against its stored hash.
    """
    return password_hash.verify(
        plain_password,
        hashed_password,
    )


def create_access_token(user_id: UUID) -> str:
    """
    Create a short-lived JWT access token.
    """

    now = datetime.now(timezone.utc)

    expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    payload: dict[str, Any] = {
        "sub": str(user_id),
        "type": "access",
        "jti": str(uuid4()),
        "iat": now,
        "exp": expire,
    }

    return jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )


def create_refresh_token(
    user_id: UUID,
) -> str:
    now = datetime.now(timezone.utc)

    expire = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    jti = str(uuid4())

    payload: dict[str, Any] = {
        "sub": str(user_id),
        "type": "refresh",
        "jti": jti,
        "iat": now,
        "exp": expire,
    }

    token = jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )

    return token


def decode_token(
    token: str,
    expected_type: str,
) -> UUID:
    """
    Decode and validate a JWT.

    Returns the user UUID contained in the `sub` claim.
    """

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )

        token_type = payload.get("type")

        if token_type != expected_type:
            raise ValueError("Invalid token type")

        subject = payload.get("sub")

        if not subject:
            raise ValueError("Token subject is missing")

        return UUID(subject)

    except (JWTError, ValueError):
        raise ValueError("Invalid or expired token") from None


def decode_refresh_token(token: str) -> tuple[UUID, str]:
    """
    Decode and validate a refresh token.

    Returns:
        (user_id, jti)
    """

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )

        if payload.get("type") != "refresh":
            raise ValueError("Invalid token type")

        subject = payload.get("sub")
        jti = payload.get("jti")

        if not subject:
            raise ValueError("Token subject is missing")

        if not jti:
            raise ValueError("Token JTI is missing")

        return UUID(subject), jti

    except (JWTError, ValueError):
        raise ValueError("Invalid or expired refresh token") from None
