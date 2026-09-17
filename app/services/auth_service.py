from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    InactiveUserException,
    InvalidCredentialsException,
    RoleNotFoundException,
    UserAlreadyExistsException,
)

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    hash_password,
    verify_password,
)

from app.services.token_service import (
    get_refresh_token_user,
    revoke_refresh_token,
    revoke_all_refresh_tokens,
    store_refresh_token,
)

from app.db.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.user import UserCreate

from redis.asyncio import Redis

from app.core.config import settings


class AuthService:
    def __init__(
        self,
        db: AsyncSession,
        redis: Redis,
    ):
        self.repository = UserRepository(db)
        self.redis = redis

    async def register(
        self,
        user_data: UserCreate,
    ) -> User:
        """
        Register a new user.
        """

        # 1. Check email
        email = str(user_data.email).strip().lower()
        existing_email = await self.repository.get_by_email(email)

        if existing_email:
            raise UserAlreadyExistsException("Email is already registered.")

        # 2. Check username
        existing_username = await self.repository.get_by_username(user_data.username)

        if existing_username:
            raise UserAlreadyExistsException("Username is already registered.")

        # 3. Get or provision the default USER role
        role = await self.repository.get_or_create_role("USER")

        # 4. Hash password
        hashed_password = hash_password(user_data.password)

        # 5. Create SQLAlchemy model
        new_user = User(
            username=user_data.username,
            email=email,
            hashed_password=hashed_password,
            role_id=role.id,
        )

        # 6. Persist user
        return await self.repository.create(new_user)

    async def login(
        self,
        login_data: LoginRequest,
    ) -> TokenResponse:
        """
        Authenticate user and generate access/refresh tokens.
        """
        email = str(login_data.email).strip().lower()
        user = await self.repository.get_by_email(email)

        # Don't reveal whether email exists.
        if user is None:
            raise InvalidCredentialsException("Invalid email or password.")

        # Verify password
        password_valid = verify_password(
            login_data.password,
            user.hashed_password,
        )

        if not password_valid:
            raise InvalidCredentialsException("Invalid email or password.")

        # Check account status
        if not user.is_active:
            raise InactiveUserException("User account is inactive.")

        # Create tokens
        access_token = create_access_token(user.id)

        refresh_token = create_refresh_token(user.id)
        _, refresh_jti = decode_refresh_token(refresh_token)

        await store_refresh_token(
            redis=self.redis,
            jti=refresh_jti,
            user_id=str(user.id),
            ttl_seconds=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
        )

    async def refresh_access_token(
        self,
        refresh_token: str,
    ) -> TokenResponse:

        try:
            user_id, jti = decode_refresh_token(refresh_token)

        except ValueError:
            raise InvalidCredentialsException(
                "Invalid or expired refresh token."
            ) from None

        stored_user_id = await get_refresh_token_user(
            self.redis,
            jti,
        )

        if stored_user_id is None:
            raise InvalidCredentialsException(
                "Refresh token has been revoked or already used."
            )

        if stored_user_id != str(user_id):
            raise InvalidCredentialsException("Invalid refresh token.")

        user = await self.repository.get_by_id(user_id)

        if user is None:
            raise InvalidCredentialsException("Invalid refresh token.")

        if not user.is_active:
            raise InactiveUserException("User account is inactive.")

        # Revoke old refresh token
        await revoke_refresh_token(
            self.redis,
            jti,
        )

        # Create new tokens
        access_token = create_access_token(user.id)

        new_refresh_token = create_refresh_token(user.id)
        _, new_refresh_jti = decode_refresh_token(new_refresh_token)

        # Store new refresh token
        await store_refresh_token(
            redis=self.redis,
            jti=new_refresh_jti,
            user_id=str(user.id),
            ttl_seconds=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
        )

    async def logout(
        self,
        refresh_token: str,
    ) -> None:

        try:
            _, jti = decode_refresh_token(refresh_token)

        except ValueError:
            # Logout should be idempotent.
            # If token is already invalid/revoked,
            # there is nothing more to do.
            return

        await revoke_refresh_token(
            self.redis,
            jti,
        )

    async def logout_all(self, user_id) -> None:
        await revoke_all_refresh_tokens(self.redis, str(user_id))

    async def change_password(
        self,
        user_id,
        current_password: str,
        new_password: str,
    ) -> None:
        user = await self.repository.get_by_id(user_id)

        if user is None or not verify_password(
            current_password,
            user.hashed_password,
        ):
            raise InvalidCredentialsException("Invalid current password.")

        await self.repository.update_password(
            user,
            hash_password(new_password),
        )
        # A password change invalidates every refresh session so a previously
        # issued refresh token cannot be used to regain a session.
        await revoke_all_refresh_tokens(self.redis, str(user.id))
