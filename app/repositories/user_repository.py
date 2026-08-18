from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.role import Role
from app.db.models.user import User


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(
        self,
        user_id: UUID,
    ) -> User | None:
        result = await self.db.execute(
            select(User).where(
                User.id == user_id,
                User.is_deleted.is_(False),
            )
        )

        return result.scalar_one_or_none()

    async def get_by_email(
        self,
        email: str,
    ) -> User | None:
        result = await self.db.execute(select(User).where(User.email == email))

        return result.scalar_one_or_none()

    async def get_by_username(
        self,
        username: str,
    ) -> User | None:
        result = await self.db.execute(select(User).where(User.username == username))

        return result.scalar_one_or_none()

    async def get_role_by_name(
        self,
        name: str,
    ) -> Role | None:
        result = await self.db.execute(select(Role).where(Role.name == name))

        return result.scalar_one_or_none()

    async def create(
        self,
        user: User,
    ) -> User:
        self.db.add(user)

        await self.db.commit()

        await self.db.refresh(user)

        return user
