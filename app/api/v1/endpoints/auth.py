from typing import Annotated

from app.api.dependencies.auth import get_current_active_user
from app.core import redis
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.database import get_db
from app.api.dependencies.rate_limit import login_rate_limit
from app.core.exceptions import (
    InactiveUserException,
    InvalidCredentialsException,
    RoleNotFoundException,
    UserAlreadyExistsException,
)
from app.db.models.user import User
from app.schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    RefreshTokenRequest,
    TokenResponse,
    LogoutResponse,
    ChangePasswordResponse,
)
from app.schemas.user import UserCreate, UserResponse
from app.services.auth_service import AuthService

from redis.asyncio import Redis
from app.core.redis import get_redis

router = APIRouter()


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    user_data: UserCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[Redis, Depends(get_redis)],
) -> UserResponse:

    service = AuthService(
        db=db,
        redis=redis,
    )

    try:
        user = await service.register(user_data)

    except UserAlreadyExistsException as exc:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    except RoleNotFoundException as exc:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

    return UserResponse.model_validate(user)


@router.post(
    "/login",
    response_model=TokenResponse,
)
async def login(
    _rate_limit: Annotated[None, Depends(login_rate_limit())],
    form_data: Annotated[
        OAuth2PasswordRequestForm,
        Depends(),
    ],
    db: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[Redis, Depends(get_redis)],
) -> TokenResponse:

    service = AuthService(
        db=db,
        redis=redis,
    )

    login_data = LoginRequest(
        email=form_data.username,
        password=form_data.password,
    )

    try:
        return await service.login(login_data)

    except InvalidCredentialsException as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={
                "WWW-Authenticate": "Bearer",
            },
        ) from exc

    except InactiveUserException as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc


@router.post(
    "/refresh",
    response_model=TokenResponse,
)
async def refresh_token(
    request: RefreshTokenRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[Redis, Depends(get_redis)],
) -> TokenResponse:

    service = AuthService(
        db=db,
        redis=redis,
    )

    try:
        return await service.refresh_access_token(request.refresh_token)

    except InvalidCredentialsException as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={
                "WWW-Authenticate": "Bearer",
            },
        ) from exc

    except InactiveUserException as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc


@router.post(
    "/logout",
    response_model=LogoutResponse,
)
async def logout(
    request: RefreshTokenRequest,
    redis: Annotated[Redis, Depends(get_redis)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> LogoutResponse:

    service = AuthService(
        db=db,
        redis=redis,
    )

    await service.logout(request.refresh_token)

    return LogoutResponse()


@router.post(
    "/change-password",
    response_model=ChangePasswordResponse,
)
async def change_password(
    request: ChangePasswordRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[Redis, Depends(get_redis)],
    current_user: Annotated[
        User,
        Depends(get_current_active_user),
    ],
) -> ChangePasswordResponse:

    service = AuthService(
        db=db,
        redis=redis,
    )

    try:
        await service.change_password(
            current_user.id,
            request.current_password,
            request.new_password,
        )
    except InvalidCredentialsException as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={
                "WWW-Authenticate": "Bearer",
            },
        ) from exc

    return ChangePasswordResponse()

@router.post(
    "/logout-all",
    response_model=LogoutResponse,
)
async def logout_all(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[Redis, Depends(get_redis)],
) -> LogoutResponse:
    service = AuthService(db=db, redis=redis)
    await service.logout_all(current_user.id)
    return LogoutResponse(message="All sessions have been logged out")
