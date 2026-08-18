from sqlalchemy.orm import DeclarativeBase

from app.db.models.mixins import TimestampMixin


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""


class BaseModel(Base, TimestampMixin):
    """Base model shared by application models."""

    __abstract__ = True
