from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PermissionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str | None = None


class RoleCreate(BaseModel):
    name: str = Field(min_length=2, max_length=50)


class RolePermissionUpdate(BaseModel):
    permission_name: str = Field(min_length=2, max_length=100)
    description: str | None = Field(default=None, max_length=255)


class RoleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    permissions: list[PermissionResponse] = Field(default_factory=list)
