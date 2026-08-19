from typing import Annotated

from fastapi import APIRouter, Depends
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_current_active_user
from app.api.dependencies.database import get_db
from app.core.redis import get_redis
from app.db.models.user import User
from app.schemas.user import UserCreate, UserResponse
from app.services.auth_service import AuthService


router = APIRouter()


@router.post(
    "/",
    response_model=UserResponse,
    status_code=201,
)
async def register_user(
    user_data: UserCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[Redis, Depends(get_redis)],
) -> UserResponse:
    service = AuthService(db=db, redis=redis)
    user = await service.register(user_data)

    return UserResponse.model_validate(user)


@router.get(
    "/me",
    response_model=UserResponse,
)
async def get_me(
    current_user: Annotated[
        User,
        Depends(get_current_active_user),
    ],
) -> UserResponse:
    return UserResponse.model_validate(current_user)
