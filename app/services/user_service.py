from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserUpdate


class UserService:
    def __init__(self, db: AsyncSession):
        self.repository = UserRepository(db)

    async def update_user(self, user_id: UUID, data: UserUpdate):
        user = await self.repository.get_by_id(user_id)
        if user is None:
            raise HTTPException(status_code=404, detail="User not found.")

        values = data.model_dump(exclude_unset=True)
        if "email" in values and values["email"] is not None:
            email = str(values["email"]).strip().lower()
            existing = await self.repository.get_by_email(email)
            if existing and existing.id != user.id:
                raise HTTPException(status_code=409, detail="Email is already registered.")
            values["email"] = email

        if "username" in values and values["username"] is not None:
            username = values["username"].strip()
            existing = await self.repository.get_by_username(username)
            if existing and existing.id != user.id:
                raise HTTPException(status_code=409, detail="Username is already registered.")
            values["username"] = username

        return await self.repository.update(user, values)

    async def delete_user(self, user_id: UUID):
        user = await self.repository.get_by_id(user_id)
        if user is None:
            raise HTTPException(status_code=404, detail="User not found.")
        return await self.repository.soft_delete(user)
