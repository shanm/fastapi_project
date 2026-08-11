# User management endpoints
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.user import UserCreate, UserResponse
from app.db.session import get_db
from app.services.user_service import create_user

router = APIRouter()

@router.post("/", response_model=UserResponse)
async def register_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    return await create_user(user, db)
