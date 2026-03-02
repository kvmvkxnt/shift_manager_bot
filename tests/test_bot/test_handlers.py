import random
from datetime import datetime, timezone
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram.types import Message
from aiogram.types import User as TgUser
from sqlalchemy.ext.asyncio import AsyncSession

from shift_manager_bot.database.models.user import User, UserRole


def make_tg_user(user_id: int = 123456789) -> TgUser:
    return TgUser(id=user_id, is_bot=False, first_name="Test", username="testuser")


def make_message(tg_user: TgUser, text: str = "/start") -> MagicMock:
    message = MagicMock(spec=Message)
    message.from_user = tg_user
    message.chat = MagicMock()
    message.chat.id = tg_user.id
    message.text = text
    message.answer = AsyncMock()
    return message


@pytest.fixture
async def pending_user(db_session: AsyncSession) -> User:
    user = User(
        telegram_id=random.randint(3200000000, 3299999999),
        full_name="Pending User",
        role=UserRole.PENDING,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def employee_user(db_session: AsyncSession) -> User:
    user = User(
        telegram_id=random.randint(3300000000, 3399999999),
        full_name="Employee User",
        role=UserRole.EMPLOYEE,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def manager_user(db_session: AsyncSession) -> User:
    user = User(
        telegram_id=random.randint(3400000000, 3499999999),
        full_name="Manager User",
        role=UserRole.MANAGER,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


# /start test
@pytest.mark.asyncio
async def test_start_pending_user_asks_for_invite_code(
    db_session: AsyncSession, pending_user: User
) -> None:
    from shift_manager_bot.bot.handlers.common import cmd_start

    tg_user = make_tg_user(user_id=pending_user.telegram_id)
    message = make_message(tg_user)
    data: dict[str, Any] = {"session": db_session, "user": pending_user}

    await cmd_start(message, data)

    message.answer.assert_called_once()
    response_text: str = message.answer.call_args[0][0]
    assert "invite" in response_text.lower() or "code" in response_text.lower()


@pytest.mark.asyncio
async def test_start_employee_sees_employee_menu(
    db_session: AsyncSession, employee_user: User
) -> None:
    from shift_manager_bot.bot.handlers.common import cmd_start

    tg_user = make_tg_user(user_id=employee_user.telegram_id)
    message = make_message(tg_user)
    data: dict[str, Any] = {"session": db_session, "user": employee_user}

    await cmd_start(message, data)

    message.answer.assert_called_once()
    response_text: str = message.answer.call_args[0][0]
    assert "shift" in response_text.lower() or "task" in response_text.lower()


@pytest.mark.asyncio
async def test_start_manager_sees_manager_menu(
    db_session: AsyncSession, manager_user: User
) -> None:
    from shift_manager_bot.bot.handlers.common import cmd_start

    tg_user = make_tg_user(user_id=manager_user.telegram_id)
    message = make_message(tg_user)
    data: dict[str, Any] = {"session": db_session, "user": manager_user}

    await cmd_start(message, data)

    message.answer.assert_called_once()
    response_text: str = message.answer.call_args[0][0]
    assert "team" in response_text.lower() or "create" in response_text.lower()


# /help tests
@pytest.mark.asyncio
async def test_help_pending_user(db_session: AsyncSession, pending_user: User) -> None:
    from shift_manager_bot.bot.handlers.common import cmd_help

    tg_user = make_tg_user(user_id=pending_user.telegram_id)
    message = make_message(tg_user, text="/help")
    data: dict[str, Any] = {"session": db_session, "user": pending_user}

    await cmd_help(message, data)

    message.answer.assert_called_once()


@pytest.mark.asyncio
async def test_help_employee(db_session: AsyncSession, employee_user: User) -> None:
    from shift_manager_bot.bot.handlers.common import cmd_help

    tg_user = make_tg_user(user_id=employee_user.telegram_id)
    message = make_message(tg_user, text="/help")
    data: dict[str, Any] = {"session": db_session, "user": employee_user}

    await cmd_help(message, data)

    message.answer.assert_called_once()
    response_text: str = message.answer.call_args[0][0]
    assert "shift" in response_text.lower() or "task" in response_text.lower()


@pytest.mark.asyncio
async def test_help_manager(db_session: AsyncSession, manager_user: User) -> None:
    from shift_manager_bot.bot.handlers.common import cmd_help

    tg_user = make_tg_user(user_id=manager_user.telegram_id)
    message = make_message(tg_user, text="/help")
    data: dict[str, Any] = {"session": db_session, "user": manager_user}

    await cmd_help(message, data)

    message.answer.assert_called_once()
    response_text: str = message.answer.call_args[0][0]
    assert "create" in response_text.lower() or "team" in response_text.lower()


# Invite code handling tests
@pytest.mark.asyncio
async def test_pending_user_enters_valid_code(
    db_session: AsyncSession,
    pending_user: User,
) -> None:
    from shift_manager_bot.bot.handlers.common import handle_invite_code
    from shift_manager_bot.services.invite_code_service import InviteCodeService

    owner = User(
        telegram_id=random.randint(4500000000, 4599999999),
        full_name="Owner",
        role=UserRole.OWNER,
    )
    db_session.add(owner)
    await db_session.commit()
    await db_session.refresh(owner)

    invite_service = InviteCodeService()
    code = await invite_service.generate(
        db_session,
        role=UserRole.EMPLOYEE,
        created_by=owner.id,
    )

    tg_user = make_tg_user(user_id=pending_user.telegram_id)
    message = make_message(tg_user, text=code.code)
    data: dict[str, Any] = {"session": db_session, "user": pending_user}

    await handle_invite_code(message, data)

    message.answer.assert_called_once()
    response_text: str = message.answer.call_args[0][0]
    assert "welcome" in response_text.lower() or "success" in response_text.lower()

    await db_session.refresh(pending_user)
    assert pending_user.role == UserRole.EMPLOYEE


@pytest.mark.asyncio
async def test_pending_user_enters_invalid_code(
    db_session: AsyncSession,
    pending_user: User,
) -> None:
    from shift_manager_bot.bot.handlers.common import handle_invite_code

    tg_user = make_tg_user(user_id=pending_user.telegram_id)
    message = make_message(tg_user, text="INVALID123")
    data: dict[str, Any] = {"session": db_session, "user": pending_user}

    await handle_invite_code(message, data)

    message.answer.assert_called_once()
    response_text: str = message.answer.call_args[0][0]
    assert "invalid" in response_text.lower() or "wrong" in response_text.lower()

    await db_session.refresh(pending_user)
    assert pending_user.role == UserRole.PENDING


@pytest.mark.asyncio
async def test_pending_user_enters_expired_code(
    db_session: AsyncSession,
    pending_user: User,
) -> None:
    from datetime import timedelta

    from shift_manager_bot.bot.handlers.common import handle_invite_code
    from shift_manager_bot.services.invite_code_service import InviteCodeService

    owner = User(
        telegram_id=random.randint(4600000000, 4699999999),
        full_name="Owner",
        role=UserRole.OWNER,
    )
    db_session.add(owner)
    await db_session.commit()
    await db_session.refresh(owner)

    invite_service = InviteCodeService()
    code = await invite_service.generate(
        db_session,
        role=UserRole.EMPLOYEE,
        created_by=owner.id,
        expires_at=datetime.now(timezone.utc) - timedelta(days=1),
    )

    tg_user = make_tg_user(user_id=pending_user.telegram_id)
    message = make_message(tg_user, text=code.code)
    data: dict[str, Any] = {"session": db_session, "user": pending_user}

    await handle_invite_code(message, data)

    message.answer.assert_called_once()
    response_text: str = message.answer.call_args[0][0]
    assert "expired" in response_text.lower() or "invalid" in response_text.lower()

    await db_session.refresh(pending_user)
    assert pending_user.role == UserRole.PENDING
