from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.role import Role
from app.db.models.user import User


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, user_id: UUID, include_deleted: bool = False) -> User | None:
        query = select(User).where(User.id == user_id)
        if not include_deleted:
            query = query.where(User.is_deleted.is_(False))
        result = await self.db.execute(query.options(selectinload(User.role)))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str, include_deleted: bool = False) -> User | None:
        query = select(User).where(User.email == email)
        if not include_deleted:
            query = query.where(User.is_deleted.is_(False))
        result = await self.db.execute(query.options(selectinload(User.role)))
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str, include_deleted: bool = False) -> User | None:
        query = select(User).where(User.username == username)
        if not include_deleted:
            query = query.where(User.is_deleted.is_(False))
        result = await self.db.execute(query.options(selectinload(User.role)))
        return result.scalar_one_or_none()

    async def list_users(
        self,
        page: int = 1,
        page_size: int = 20,
        username: str | None = None,
        email: str | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> tuple[list[User], int]:
        filters = [User.is_deleted.is_(False)]
        if username:
            filters.append(User.username.ilike(f"%{username.strip()}%"))
        if email:
            filters.append(User.email.ilike(f"%{email.strip().lower()}%"))

        total = await self.db.scalar(select(func.count(User.id)).where(*filters)) or 0
        sort_column = {
            "username": User.username,
            "email": User.email,
            "created_at": User.created_at,
            "updated_at": User.updated_at,
        }.get(sort_by, User.created_at)
        ordering = sort_column.asc() if sort_order.lower() == "asc" else sort_column.desc()

        result = await self.db.execute(
            select(User)
            .where(*filters)
            .options(selectinload(User.role))
            .order_by(ordering)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(result.scalars().all()), total

    async def get_role_by_name(self, name: str) -> Role | None:
        result = await self.db.execute(select(Role).where(Role.name == name.upper()))
        return result.scalar_one_or_none()

    async def get_or_create_role(self, name: str) -> Role:
        role = await self.get_role_by_name(name)
        if role is None:
            role = Role(name=name.strip().upper())
            self.db.add(role)
            await self.db.flush()
        return role

    async def create(self, user: User) -> User:
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def update_password(self, user: User, hashed_password: str) -> User:
        user.hashed_password = hashed_password
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def update(self, user: User, values: dict) -> User:
        for field, value in values.items():
            setattr(user, field, value)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def soft_delete(self, user: User) -> User:
        user.is_deleted = True
        user.is_active = False
        await self.db.commit()
        await self.db.refresh(user)
        return user
