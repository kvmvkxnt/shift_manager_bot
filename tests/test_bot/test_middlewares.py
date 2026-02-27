from typing import Any
import random
import pytest
from unittest.mock import AsyncMock, MagicMock
from aiogram.types import Message, Chat, User as TgUser
from sqlalchemy.ext.asyncio import AsyncSession

from shift_manager_bot.bot.middlewares.auth import AuthMiddleware
from shift_manager_bot.bot.middlewares.db import DbSessionMiddleware
from shift_manager_bot.database.models.user import User, UserRole


def make_tg_user(user_id: int = 123456789) -> TgUser:
    return TgUser(id=user_id, is_bot=False, first_name="Test", username="testuser")


def make_message(tg_user: TgUser) -> Message:
    chat = Chat(id=tg_user.id, type="private")
    message = MagicMock(spec=Message)
    message.from_user = tg_user
    message.chat = chat
    return message


@pytest.mark.asyncio
async def test_db_middleware_injects_session(db_session: AsyncSession) -> None:
    handler = AsyncMock()
    event = make_message(make_tg_user())
    data: dict[str, Any] = {}

    async def mock_session_factory() -> AsyncSession:
        return db_session

    middleware = DbSessionMiddleware(session_factory=mock_session_factory)
    await middleware(handler, event, data)

    assert "session" in data
    handler.assert_called_once()


@pytest.mark.asyncio
async def test_auth_middleware_creates_new_user(db_session: AsyncSession) -> None:
    telegram_id = random.randint(3000000000, 3099999999)
    tg_user = make_tg_user(user_id=telegram_id)
    message = make_message(tg_user)

    handler = AsyncMock()
    data: dict[str, Any] = {"session": db_session}

    middleware = AuthMiddleware()
    await middleware(handler, message, data)

    assert "user" in data
    assert data["user"].telegram_id == telegram_id
    assert data["user"].role == UserRole.PENDING
    handler.assert_called_once()


@pytest.mark.asyncio
async def test_auth_middleware_loads_existing_user(db_session: AsyncSession) -> None:
    telegram_id = random.randint(3100000000, 3199999999)
    existing_user = User(
        telegram_id=telegram_id, full_name="Existing", role=UserRole.MANAGER
    )
    db_session.add(existing_user)
    await db_session.commit()
    await db_session.refresh(existing_user)

    tg_user = make_tg_user(user_id=telegram_id)
    message = make_message(tg_user)

    handler = AsyncMock()
    data: dict[str, Any] = {"session": db_session}

    middleware = AuthMiddleware()
    await middleware(handler, message, data)

    assert data["user"].role == UserRole.MANAGER
    assert data["user"].id == existing_user.id


@pytest.mark.asyncio
async def test_auth_middleware_skips_if_no_from_user(db_session: AsyncSession) -> None:
    message = MagicMock(spec=Message)
    message.from_user = None

    handler = AsyncMock()
    data: dict[str, Any] = {"session": db_session}

    middleware = AuthMiddleware()
    await middleware(handler, message, data)

    assert "user" not in data
    handler.assert_called_once()
