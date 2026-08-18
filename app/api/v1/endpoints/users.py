from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies.auth import get_current_active_user
from app.db.models.user import User
from app.schemas.user import UserResponse


router = APIRouter()


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
