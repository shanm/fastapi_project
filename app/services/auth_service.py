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

from app.db.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.user import UserCreate

from redis.asyncio import Redis

from app.services.token_service import (
    get_refresh_token_user,
    revoke_refresh_token,
    store_refresh_token,
)

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
        existing_email = await self.repository.get_by_email(str(user_data.email))

        if existing_email:
            raise UserAlreadyExistsException("Email is already registered.")

        # 2. Check username
        existing_username = await self.repository.get_by_username(user_data.username)

        if existing_username:
            raise UserAlreadyExistsException("Username is already registered.")

        # 3. Get default USER role
        role = await self.repository.get_role_by_name("USER")

        if role is None:
            raise RoleNotFoundException("Default USER role does not exist.")

        # 4. Hash password
        hashed_password = hash_password(user_data.password)

        # 5. Create SQLAlchemy model
        new_user = User(
            username=user_data.username,
            email=str(user_data.email),
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

        user = await self.repository.get_by_email(str(login_data.email))

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

        refresh_token, refresh_jti = create_refresh_token(user.id)

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

        new_refresh_token, new_refresh_jti = create_refresh_token(user.id)

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
