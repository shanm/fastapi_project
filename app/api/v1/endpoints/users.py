from math import ceil
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_current_active_user
from app.api.dependencies.authorization import require_permission
from app.api.dependencies.database import get_db
from app.core.redis import get_redis
from app.core.idempotency import require_idempotency_key
from app.db.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserResponse, UserUpdate
from app.schemas.pagination import PaginatedResponse
from app.services.auth_service import AuthService
from app.services.user_service import UserService

router = APIRouter()


@router.post("/", response_model=UserResponse, status_code=201)
async def register_user(
    user_data: UserCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[Redis, Depends(get_redis)],
) -> UserResponse:
    user = await AuthService(db=db, redis=redis).register(user_data)
    return UserResponse.model_validate(user)


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> UserResponse:
    print(f"Current user: {current_user}")
    return UserResponse.model_validate(current_user)


@router.get("/", response_model=PaginatedResponse[UserResponse])
async def list_users(
    _: Annotated[User, Depends(require_permission("users:read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    username: str | None = Query(default=None),
    email: str | None = Query(default=None),
    sort_by: str = Query(
        default="created_at", pattern="^(username|email|created_at|updated_at)$"
    ),
    sort_order: str = Query(default="desc", pattern="^(asc|desc)$"),
) -> PaginatedResponse[UserResponse]:
    users, total = await UserRepository(db).list_users(
        page=page,
        page_size=page_size,
        username=username,
        email=email,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return PaginatedResponse(
        items=[UserResponse.model_validate(user) for user in users],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=ceil(total / page_size) if total else 0,
    )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    _: Annotated[User, Depends(require_permission("users:read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserResponse:
    user = await UserRepository(db).get_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found.")
    return UserResponse.model_validate(user)


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    _idempotency: Annotated[None, Depends(require_idempotency_key())],
    user_id: UUID,
    data: UserUpdate,
    _: Annotated[User, Depends(require_permission("users:write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserResponse:
    user = await UserService(db).update_user(user_id, data)
    return UserResponse.model_validate(user)


@router.delete("/{user_id}", response_model=UserResponse)
async def delete_user(
    _idempotency: Annotated[None, Depends(require_idempotency_key())],
    user_id: UUID,
    _: Annotated[User, Depends(require_permission("users:delete"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserResponse:
    user = await UserService(db).delete_user(user_id)
    return UserResponse.model_validate(user)
