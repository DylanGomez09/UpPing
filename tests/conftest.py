import asyncio

import httpx
import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings
from app.core.rate_limit import login_rate_limiter
from app.db.base import Base
from app.db.session import get_db
from app.main import app

TEST_DB_NAME = "app_db_test"


def _server_url() -> str:
    return settings.DATABASE_URL.rsplit("/", 1)[0] + "/postgres"


def _test_db_url() -> str:
    return settings.DATABASE_URL.rsplit("/", 1)[0] + "/" + TEST_DB_NAME


async def _create_test_db() -> None:
    server_engine = create_async_engine(_server_url(), isolation_level="AUTOCOMMIT")
    async with server_engine.connect() as conn:
        await conn.execute(text(f"DROP DATABASE IF EXISTS {TEST_DB_NAME}"))
        await conn.execute(text(f"CREATE DATABASE {TEST_DB_NAME}"))
    await server_engine.dispose()


async def _drop_test_db() -> None:
    server_engine = create_async_engine(_server_url(), isolation_level="AUTOCOMMIT")
    async with server_engine.connect() as conn:
        await conn.execute(
            text(
                "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                f"WHERE datname = '{TEST_DB_NAME}'"
            )
        )
        await conn.execute(text(f"DROP DATABASE IF EXISTS {TEST_DB_NAME}"))
    await server_engine.dispose()


@pytest.fixture(scope="session")
def _test_db():
    asyncio.run(_create_test_db())
    yield
    asyncio.run(_drop_test_db())


@pytest_asyncio.fixture
async def test_engine(_test_db):
    engine = create_async_engine(_test_db_url(), pool_pre_ping=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def client(test_engine):
    session_factory = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )

    async def override_get_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture(autouse=True)
async def _clean_state(test_engine):
    yield
    login_rate_limiter.reset()
    async with test_engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(table.delete())
