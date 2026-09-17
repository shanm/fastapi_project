from collections.abc import Callable
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_current_active_user
from app.api.dependencies.database import get_db
from app.db.models.user import User
from app.services.authorization_service import AuthorizationService


def require_role(role_name: str) -> Callable:
    async def dependency(
        current_user: Annotated[User, Depends(get_current_active_user)],
        db: Annotated[AsyncSession, Depends(get_db)],
    ) -> User:
        service = AuthorizationService(db)
        await service.require_role(current_user, role_name)
        return current_user

    return dependency


def require_permission(permission_name: str) -> Callable:
    async def dependency(
        current_user: Annotated[User, Depends(get_current_active_user)],
        db: Annotated[AsyncSession, Depends(get_db)],
    ) -> User:
        service = AuthorizationService(db)
        await service.require_permission(current_user, permission_name)
        return current_user

    return dependency
