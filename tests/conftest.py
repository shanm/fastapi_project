import pytest
from fastapi.testclient import TestClient
from redis.asyncio import Redis

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from app.main import app
from app.core.config import settings
from app.api.dependencies.database import get_db
from app.core.redis import get_redis
from app.db.models.base import Base


TEST_DATABASE_URL = settings.database_url


test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    poolclass=NullPool,
)

TestSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def override_get_db():
    async with TestSessionLocal() as session:
        yield session


@pytest.fixture(autouse=True)
async def setup_database():

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await test_engine.dispose()


@pytest.fixture
async def db_session():
    async with TestSessionLocal() as session:
        yield session


@pytest.fixture
def client() -> TestClient:

    app.dependency_overrides[get_db] = override_get_db

    async def override_get_redis() -> Redis:
        return Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            decode_responses=True,
        )

    app.dependency_overrides[get_redis] = override_get_redis

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
async def user_role(db_session):

    from app.repositories.user_repository import UserRepository
    from app.db.models.role import Role

    user_repo = UserRepository(db_session)

    role = await user_repo.get_role_by_name("USER")

    if not role:
        role = Role(name="USER")

        db_session.add(role)

        await db_session.commit()
        await db_session.refresh(role)

    return role


@pytest.fixture
def authenticated_user(client, user_role):
    client.post(
        "/api/v1/auth/register",
        json={
            "username": "john",
            "email": "john@example.com",
            "password": "Password123!",
        },
    )

    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "john@example.com",
            "password": "Password123!",
        },
    )

    return response.json()
