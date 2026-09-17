from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.authorization import require_role
from app.api.dependencies.database import get_db
from app.db.models.user import User
from app.repositories.role_repository import RoleRepository
from app.repositories.user_repository import UserRepository
from app.schemas.role import RoleCreate, RolePermissionUpdate, RoleResponse
from app.schemas.user import UserRoleUpdate

router = APIRouter()


@router.get("/", response_model=list[RoleResponse])
async def list_roles(
    _: Annotated[User, Depends(require_role("ADMIN"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[RoleResponse]:
    roles = await RoleRepository(db).list_roles()
    return [RoleResponse.model_validate(role) for role in roles]


@router.post("/", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
async def create_role(
    data: RoleCreate,
    _: Annotated[User, Depends(require_role("ADMIN"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> RoleResponse:
    repository = RoleRepository(db)
    if await repository.get_by_name(data.name):
        raise HTTPException(status_code=409, detail="Role already exists.")
    role = await repository.create(data.name)
    return RoleResponse.model_validate(role)


@router.post("/{role_id}/permissions", response_model=RoleResponse)
async def add_permission_to_role(
    role_id: UUID,
    data: RolePermissionUpdate,
    _: Annotated[User, Depends(require_role("ADMIN"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> RoleResponse:
    repository = RoleRepository(db)
    role = await repository.get_by_id(role_id)
    if role is None:
        raise HTTPException(status_code=404, detail="Role not found.")
    permission = await repository.get_or_create_permission(data.permission_name, data.description)
    role = await repository.assign_permission(role, permission)
    return RoleResponse.model_validate(role)


@router.put("/users/{user_id}", response_model=dict)
async def assign_user_role(
    user_id: UUID,
    data: UserRoleUpdate,
    _: Annotated[User, Depends(require_role("ADMIN"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found.")
    role = await RoleRepository(db).get_by_id(data.role_id)
    if role is None:
        raise HTTPException(status_code=404, detail="Role not found.")
    user.role_id = role.id
    await db.commit()
    return {"user_id": str(user.id), "role_id": str(role.id), "role": role.name}
