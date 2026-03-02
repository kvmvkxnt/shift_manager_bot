import random
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram.types import Message
from aiogram.types import User as TgUser
from sqlalchemy.ext.asyncio import AsyncSession

from shift_manager_bot.database.models.user import User, UserRole


def make_tg_user(user_id: int) -> TgUser:
    return TgUser(
        id=user_id,
        is_bot=False,
        first_name="Owner",
        username="owner",
    )


def make_message(tg_user: TgUser, text: str = "") -> MagicMock:
    message = MagicMock(spec=Message)
    message.from_user = tg_user
    message.text = text
    message.answer = AsyncMock()
    return message


@pytest.fixture
async def owner(db_session: AsyncSession) -> User:
    user = User(
        telegram_id=random.randint(4700000000, 4799999999),
        full_name="Test Owner",
        role=UserRole.OWNER,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def manager(db_session: AsyncSession) -> User:
    user = User(
        telegram_id=random.randint(4800000000, 4899999999),
        full_name="Test Manager",
        role=UserRole.MANAGER,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def employee(db_session: AsyncSession, manager: User) -> User:
    user = User(
        telegram_id=random.randint(4900000000, 4999999999),
        full_name="Test Employee",
        role=UserRole.EMPLOYEE,
        manager_id=manager.id,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


# /admin tests
@pytest.mark.asyncio
async def test_admin_shows_overview(
    db_session: AsyncSession,
    owner: User,
    manager: User,
    employee: User,
) -> None:
    from shift_manager_bot.bot.handlers.owner import cmd_admin

    tg_user = make_tg_user(owner.telegram_id)
    message = make_message(tg_user)
    data: dict[str, Any] = {"session": db_session, "user": owner}

    await cmd_admin(message, data)

    message.answer.assert_called_once()
    response_text: str = message.answer.call_args[0][0]
    assert "manager" in response_text.lower() or "team" in response_text.lower()


# /invite tests
@pytest.mark.asyncio
async def test_owner_can_generate_manager_invite(
    db_session: AsyncSession,
    owner: User,
) -> None:
    from shift_manager_bot.bot.handlers.owner import cmd_invite_manager

    tg_user = make_tg_user(owner.telegram_id)
    message = make_message(tg_user)
    data: dict[str, Any] = {"session": db_session, "user": owner}

    await cmd_invite_manager(message, data)

    message.answer.assert_called_once()
    response_text: str = message.answer.call_args[0][0]
    assert "code" in response_text.lower() or "invite" in response_text.lower()


@pytest.mark.asyncio
async def test_owner_can_generate_employee_invite(
    db_session: AsyncSession,
    owner: User,
    manager: User,
) -> None:
    from shift_manager_bot.bot.handlers.owner import cmd_invite_employee

    tg_user = make_tg_user(owner.telegram_id)
    message = make_message(tg_user)
    data: dict[str, Any] = {"session": db_session, "user": owner}

    await cmd_invite_employee(message, data)

    message.answer.assert_called_once()


# /all_teams tests
@pytest.mark.asyncio
async def test_all_teams_shows_managers_and_employees(
    db_session: AsyncSession,
    owner: User,
    manager: User,
    employee: User,
) -> None:
    from shift_manager_bot.bot.handlers.owner import cmd_all_teams

    tg_user = make_tg_user(owner.telegram_id)
    message = make_message(tg_user)
    data: dict[str, Any] = {"session": db_session, "user": owner}

    await cmd_all_teams(message, data)

    message.answer.assert_called_once()
    response_text: str = message.answer.call_args[0][0]
    assert manager.full_name in response_text
    assert employee.full_name in response_text


@pytest.mark.asyncio
async def test_all_teams_empty(
    db_session: AsyncSession,
    owner: User,
) -> None:
    from shift_manager_bot.bot.handlers.owner import cmd_all_teams

    tg_user = make_tg_user(owner.telegram_id)
    message = make_message(tg_user)
    data: dict[str, Any] = {"session": db_session, "user": owner}

    await cmd_all_teams(message, data)

    message.answer.assert_called_once()
    response_text: str = message.answer.call_args[0][0]
    assert "no" in response_text.lower() or "empty" in response_text.lower()


# /org_stats tests
@pytest.mark.asyncio
async def test_org_stats_shows_summary(
    db_session: AsyncSession,
    owner: User,
    manager: User,
    employee: User,
) -> None:
    from shift_manager_bot.bot.handlers.owner import cmd_org_stats

    tg_user = make_tg_user(owner.telegram_id)
    message = make_message(tg_user)
    data: dict[str, Any] = {"session": db_session, "user": owner}

    await cmd_org_stats(message, data)

    message.answer.assert_called_once()
    response_text: str = message.answer.call_args[0][0]
    assert "manager" in response_text.lower() or "employee" in response_text.lower()
