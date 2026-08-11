from app.db.models.user import User
from sqlalchemy.ext.asyncio import AsyncSession


async def create_user(user_data, db: AsyncSession):
    new_user = User(email=user_data.email, hashed_password="hashed")
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user
