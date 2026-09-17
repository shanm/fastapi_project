from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.user import User
from app.repositories.role_repository import RoleRepository


class AuthorizationService:
    def __init__(self, db: AsyncSession):
        self.repository = RoleRepository(db)

    async def user_has_role(self, user: User, role_name: str) -> bool:
        role = await self.repository.get_by_id(user.role_id)
        return role is not None and role.name.upper() == role_name.upper()

    async def user_has_permission(self, user: User, permission_name: str) -> bool:
        role = await self.repository.get_by_id(user.role_id)
        if role is None:
            return False

        # [(p.name, permission_name, p.name == permission_name) for p in role.permissions]
        return any(p.name == permission_name for p in role.permissions)

    async def require_role(self, user: User, role_name: str) -> None:
        if not await self.user_has_role(user, role_name):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient role permissions.",
            )

    async def require_permission(self, user: User, permission_name: str) -> None:
        print(
            f"Checking permission for user {user.id} and permission {permission_name}"
        )
        print(f"User role ID: {user.role_id}")
        role = await self.repository.get_by_id(user.role_id)
        print(f"User role: {role.name if role else 'None'}")
        if not await self.user_has_permission(user, permission_name):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions.",
            )
