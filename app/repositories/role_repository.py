from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.permission import Permission
from app.db.models.role import Role


class RoleRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_name(self, name: str) -> Role | None:
        result = await self.db.execute(
            select(Role).where(Role.name == name.upper()).options(selectinload(Role.permissions))
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, role_id: UUID) -> Role | None:
        result = await self.db.execute(
            select(Role).where(Role.id == role_id).options(selectinload(Role.permissions))
        )
        return result.scalar_one_or_none()

    async def list_roles(self) -> list[Role]:
        result = await self.db.execute(
            select(Role).order_by(Role.name).options(selectinload(Role.permissions))
        )
        return list(result.scalars().unique().all())

    async def create(self, name: str) -> Role:
        role = Role(name=name.strip().upper())
        self.db.add(role)
        await self.db.commit()
        await self.db.refresh(role)
        return role

    async def get_permission(self, name: str) -> Permission | None:
        result = await self.db.execute(select(Permission).where(Permission.name == name))
        return result.scalar_one_or_none()

    async def get_or_create_permission(self, name: str, description: str | None = None) -> Permission:
        permission = await self.get_permission(name)
        if permission is None:
            permission = Permission(name=name, description=description)
            self.db.add(permission)
            await self.db.flush()
        return permission

    async def assign_permission(self, role: Role, permission: Permission) -> Role:
        if permission not in role.permissions:
            role.permissions.append(permission)
            await self.db.commit()
            await self.db.refresh(role)
        return role
