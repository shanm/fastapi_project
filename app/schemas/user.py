from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    """
    Data required when creating a new user.
    """

    username: str = Field(
        ...,
        min_length=3,
        max_length=100,
    )

    email: EmailStr

    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
    )


class UserUpdate(BaseModel):
    """
    Fields that can be updated by the user.
    All fields are optional because this is a PATCH-style update.
    """

    username: str | None = Field(
        default=None,
        min_length=3,
        max_length=100,
    )

    email: EmailStr | None = None


class UserResponse(BaseModel):
    """
    Public representation of a user.
    Sensitive fields such as password/hash are intentionally excluded.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    username: str
    email: EmailStr
    is_active: bool
    is_deleted: bool
    role_id: UUID
    created_at: datetime
    updated_at: datetime
