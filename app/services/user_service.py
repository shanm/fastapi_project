from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.user_repository import UserRepository


class UserService:
    def __init__(self, db: AsyncSession):
        self.repository = UserRepository(db)
