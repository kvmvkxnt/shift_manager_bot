from typing import AsyncGenerator
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from shift_manager_bot.config import settings
from shift_manager_bot.database.base import Base
from shift_manager_bot.database.models import shift, task, user, invite_code  # noqa: ignore

engine = create_async_engine(settings.test_db_url, poolclass=NullPool)
test_session_factory = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with engine.connect() as connection:
        await connection.begin()
        await connection.begin_nested()  # savepoint

        session = AsyncSession(
            bind=connection,
            expire_on_commit=False,
        )

        try:
            yield session
        finally:
            await session.close()
            await connection.rollback()  # rolls back everything, including commits
