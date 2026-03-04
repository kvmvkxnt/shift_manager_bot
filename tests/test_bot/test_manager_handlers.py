import random
from datetime import datetime, timedelta, timezone
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import CallbackQuery, Message
from aiogram.types import User as TgUser
from sqlalchemy.ext.asyncio import AsyncSession

from shift_manager_bot.bot.states import CreateShiftStates, CreateTaskStates
from shift_manager_bot.database.models.shift import Shift
from shift_manager_bot.database.models.task import Task, TaskStatus
from shift_manager_bot.database.models.user import User, UserRole


def make_tg_user(user_id: int) -> TgUser:
    return TgUser(id=user_id, is_bot=False, first_name="Manager", username="manager")


def make_message(tg_user: TgUser, text: str = "") -> MagicMock:
    message = MagicMock(spec=Message)
    message.from_user = tg_user
    message.text = text
    message.answer = AsyncMock()
    return message


def make_callback(tg_user: TgUser, data: str = "") -> MagicMock:
    callback = MagicMock(spec=CallbackQuery)
    callback.from_user = tg_user
    callback.data = data
    callback.answer = AsyncMock()
    callback.message = MagicMock()
    callback.message.edit_text = AsyncMock()
    callback.message.answer = AsyncMock()
    return callback


async def make_fsm_context() -> FSMContext:
    storage = MemoryStorage()
    from aiogram.fsm.storage.base import StorageKey

    key = StorageKey(bot_id=1, chat_id=1, user_id=1)
    return FSMContext(storage=storage, key=key)


@pytest.fixture
async def manager(db_session: AsyncSession) -> User:
    user = User(
        telegram_id=random.randint(3700000000, 3799999999),
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
        telegram_id=random.randint(3800000000, 3899999999),
        full_name="Test Employee",
        role=UserRole.EMPLOYEE,
        manager_id=manager.id,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


# /my_team tests
@pytest.mark.asyncio
async def test_my_team_shows_employees(
    db_session: AsyncSession, manager: User, employee: User
) -> None:
    from shift_manager_bot.bot.handlers.manager import cmd_my_team

    tg_user = make_tg_user(manager.telegram_id)
    message = make_message(tg_user)

    await cmd_my_team(message, manager, db_session)

    message.answer.assert_called_once()
    response_text: str = message.answer.call_args[0][0]
    assert employee.full_name in response_text


@pytest.mark.asyncio
async def test_my_team_empty(db_session: AsyncSession, manager: User) -> None:
    from shift_manager_bot.bot.handlers.manager import cmd_my_team

    tg_user = make_tg_user(manager.telegram_id)
    message = make_message(tg_user)

    await cmd_my_team(message, manager, db_session)

    message.answer.assert_called_once()
    response_text: str = message.answer.call_args[0][0]
    assert "no" in response_text or "empty" in response_text


# Create shift FSM tests
@pytest.mark.asyncio
async def test_create_shift_start(manager: User) -> None:
    from shift_manager_bot.bot.handlers.manager import cmd_create_shift

    tg_user = make_tg_user(manager.telegram_id)
    message = make_message(tg_user)
    state = await make_fsm_context()

    await cmd_create_shift(message, state, manager)

    message.answer.assert_called_once()
    response_text: str = message.answer.call_args[0][0]
    assert "date" in response_text.lower()
    current_state = await state.get_state()
    assert current_state == CreateShiftStates.waiting_for_date


@pytest.mark.asyncio
async def test_create_shift_date_valid(manager: User) -> None:
    from shift_manager_bot.bot.handlers.manager import process_shift_date

    tg_user = make_tg_user(manager.telegram_id)
    tomorrow = (datetime.now(timezone.utc) + timedelta(days=1)).strftime("%Y-%m-%d")
    message = make_message(tg_user, text=tomorrow)
    state = await make_fsm_context()
    await state.set_state(CreateShiftStates.waiting_for_date)

    await process_shift_date(message, state, manager)

    message.answer.assert_called_once()
    response_text: str = message.answer.call_args[0][0]
    assert "time" in response_text.lower()
    current_state = await state.get_state()
    assert current_state == CreateShiftStates.waiting_for_time


@pytest.mark.asyncio
async def test_create_shift_date_invalid(manager: User) -> None:
    from shift_manager_bot.bot.handlers.manager import process_shift_date

    tg_user = make_tg_user(manager.telegram_id)
    message = make_message(tg_user, text="not-a-date")
    state = await make_fsm_context()
    await state.set_state(CreateShiftStates.waiting_for_date)

    await process_shift_date(message, state, manager)

    message.answer.assert_called_once()
    response_text: str = message.answer.call_args[0][0]
    assert "invalid" in response_text.lower() or "format" in response_text.lower()
    current_state = await state.get_state()
    assert current_state == CreateShiftStates.waiting_for_date


@pytest.mark.asyncio
async def test_create_shift_time_valid(manager: User) -> None:
    from shift_manager_bot.bot.handlers.manager import process_shift_time

    tg_user = make_tg_user(manager.telegram_id)
    message = make_message(tg_user, text="09:00-17:00")
    state = await make_fsm_context()
    await state.set_state(CreateShiftStates.waiting_for_time)
    await state.update_data(date="2026-12-01")

    await process_shift_time(message, state, manager)

    message.answer.assert_called_once()
    response_text: str = message.answer.call_args[0][0]
    assert "employee" in response_text.lower() or "max" in response_text.lower()
    current_state = await state.get_state()
    assert current_state == CreateShiftStates.waiting_for_max_employees


@pytest.mark.asyncio
async def test_create_shift_time_invalid(manager: User) -> None:
    from shift_manager_bot.bot.handlers.manager import process_shift_time

    tg_user = make_tg_user(manager.telegram_id)
    message = make_message(tg_user, text="not-a-time")
    state = await make_fsm_context()
    await state.set_state(CreateShiftStates.waiting_for_time)
    await state.update_data(date="2026-12-01")

    await process_shift_time(message, state, manager)

    message.answer.assert_called_once()
    response_text: str = message.answer.call_args[0][0]
    assert "invalid" in response_text.lower() or "format" in response_text.lower()
    current_state = await state.get_state()
    assert current_state == CreateShiftStates.waiting_for_time


@pytest.mark.asyncio
async def test_create_shift_max_employees_valid(manager: User) -> None:
    from shift_manager_bot.bot.handlers.manager import process_shift_max_employees

    tg_user = make_tg_user(manager.telegram_id)
    message = make_message(tg_user, text="3")
    state = await make_fsm_context()
    await state.set_state(CreateShiftStates.waiting_for_max_employees)
    await state.update_data(date="2026-12-01", time="09:00-17:00")

    await process_shift_max_employees(message, state, manager)

    message.answer.assert_called_once()
    response_text: str = message.answer.call_args[0][0]
    assert "note" in response_text.lower() or "skip" in response_text.lower()
    current_state = await state.get_state()
    assert current_state == CreateShiftStates.waiting_for_note


@pytest.mark.asyncio
async def test_create_shift_max_employees_invalid(manager: User) -> None:
    from shift_manager_bot.bot.handlers.manager import process_shift_max_employees

    tg_user = make_tg_user(manager.telegram_id)
    message = make_message(tg_user, text="invalid number")
    state = await make_fsm_context()
    await state.set_state(CreateShiftStates.waiting_for_max_employees)
    await state.update_data(date="2026-12-01", time="09:00-17:00")

    await process_shift_max_employees(message, state, manager)

    message.answer.assert_called_once()
    current_state = await state.get_state()
    assert current_state == CreateShiftStates.waiting_for_max_employees


@pytest.mark.asyncio
async def test_create_shift_note_and_finish(
    db_session: AsyncSession, manager: User
) -> None:
    from shift_manager_bot.bot.handlers.manager import process_shift_note

    tg_user = make_tg_user(manager.telegram_id)
    message = make_message(tg_user, text="Please arrive early")
    state = await make_fsm_context()
    await state.set_state(CreateShiftStates.waiting_for_note)
    await state.update_data(date="2026-12-01", time="09:00-17:00", max_employees=3)

    await process_shift_note(message, state, manager, db_session)

    message.answer.assert_called_once()
    response_text: str = message.answer.call_args[0][0]
    assert "created" in response_text.lower() or "success" in response_text.lower()
    current_state = await state.get_state()
    assert current_state is None


@pytest.mark.asyncio
async def test_create_shift_skip_note(db_session: AsyncSession, manager: User) -> None:
    from shift_manager_bot.bot.handlers.manager import process_shift_note

    tg_user = make_tg_user(manager.telegram_id)
    message = make_message(tg_user, text="/skip")
    state = await make_fsm_context()
    await state.set_state(CreateShiftStates.waiting_for_note)
    await state.update_data(date="2026-12-01", time="09:00-17:00", max_employees=3)

    await process_shift_note(message, state, manager, db_session)

    message.answer.assert_called_once()
    response_text: str = message.answer.call_args[0][0]
    assert "created" in response_text.lower() or "success" in response_text.lower()
    current_state = await state.get_state()
    assert current_state is None


# Create task FSM tests
@pytest.mark.asyncio
async def test_create_task_start(manager: User) -> None:
    from shift_manager_bot.bot.handlers.manager import cmd_create_task

    tg_user = make_tg_user(manager.telegram_id)
    message = make_message(tg_user)
    state = await make_fsm_context()

    await cmd_create_task(message, state, manager)

    message.answer.assert_called_once()
    response_text: str = message.answer.call_args[0][0]
    assert "title" in response_text.lower()
    current_state = await state.get_state()
    assert current_state == CreateTaskStates.waiting_for_title


@pytest.mark.asyncio
async def test_create_task_title(manager: User) -> None:
    from shift_manager_bot.bot.handlers.manager import process_task_title

    tg_user = make_tg_user(manager.telegram_id)
    message = make_message(tg_user, text="Clean the kitchen")
    state = await make_fsm_context()
    await state.set_state(CreateTaskStates.waiting_for_title)

    await process_task_title(message, state, manager)

    message.answer.assert_called_once()
    response_text: str = message.answer.call_args[0][0]
    assert "description" in response_text.lower() or "skip" in response_text.lower()
    current_state = await state.get_state()
    assert current_state == CreateTaskStates.waiting_for_description


@pytest.mark.asyncio
async def test_create_task_skip_description(
    db_session: AsyncSession, manager: User, employee: User
) -> None:
    from shift_manager_bot.bot.handlers.manager import process_task_description

    tg_user = make_tg_user(manager.telegram_id)
    message = make_message(tg_user, text="/skip")
    state = await make_fsm_context()
    await state.set_state(CreateTaskStates.waiting_for_description)
    await state.update_data(title="Clean kitchen")

    await process_task_description(message, state, manager, db_session)

    message.answer.assert_called_once()
    response_text: str = message.answer.call_args[0][0]
    assert "employee" in response_text.lower() or "assign" in response_text.lower()
    current_state = await state.get_state()
    assert current_state == CreateTaskStates.waiting_for_employee


@pytest.mark.asyncio
async def test_create_task_assign_employee(manager: User, employee: User) -> None:
    from shift_manager_bot.bot.handlers.manager import process_task_employee

    tg_user = make_tg_user(manager.telegram_id)
    callback = make_callback(tg_user, data=f"assign_employee:{employee.id}")
    state = await make_fsm_context()
    await state.set_state(CreateTaskStates.waiting_for_employee)
    await state.update_data(title="Clean kitchen", description=None)

    await process_task_employee(callback, state, manager)

    callback.answer.assert_called_once()
    current_state = await state.get_state()
    assert current_state == CreateTaskStates.waiting_for_deadline


@pytest.mark.asyncio
async def test_create_task_skip_deadline(
    db_session: AsyncSession,
    manager: User,
    employee: User,
) -> None:
    from shift_manager_bot.bot.handlers.manager import process_task_deadline

    tg_user = make_tg_user(manager.telegram_id)
    message = make_message(tg_user, text="/skip")
    state = await make_fsm_context()
    await state.set_state(CreateTaskStates.waiting_for_deadline)
    await state.update_data(
        title="Clean kitchen",
        description=None,
        employee_id=employee.id,
    )

    await process_task_deadline(message, state, manager, db_session)

    message.answer.assert_called_once()
    response_text: str = message.answer.call_args[0][0]
    assert "created" in response_text.lower() or "success" in response_text.lower()
    current_state = await state.get_state()
    assert current_state is None


@pytest.mark.asyncio
async def test_create_task_with_deadline(
    db_session: AsyncSession,
    manager: User,
    employee: User,
) -> None:
    from shift_manager_bot.bot.handlers.manager import process_task_deadline

    tg_user = make_tg_user(manager.telegram_id)
    message = make_message(tg_user, text="2026-12-01 17:00")
    state = await make_fsm_context()
    await state.set_state(CreateTaskStates.waiting_for_deadline)
    await state.update_data(
        title="Clean kitchen",
        description=None,
        employee_id=employee.id,
    )

    await process_task_deadline(message, state, manager, db_session)

    message.answer.assert_called_once()
    response_text: str = message.answer.call_args[0][0]
    assert "created" in response_text.lower() or "success" in response_text.lower()
    current_state = await state.get_state()
    assert current_state is None


@pytest.mark.asyncio
async def test_manager_can_generate_employee_invite(
    db_session: AsyncSession,
    manager: User,
) -> None:
    from shift_manager_bot.bot.handlers.manager import cmd_invite

    tg_user = make_tg_user(manager.telegram_id)
    message = make_message(tg_user)

    await cmd_invite(message, manager, db_session)

    message.answer.assert_called_once()
    response_text: str = message.answer.call_args[0][0]
    assert "code" in response_text.lower() or "invite" in response_text.lower()


# manager stats test
@pytest.fixture
async def manager_shift(
    db_session: AsyncSession,
    manager: User,
    employee: User,
) -> Shift:
    shift = Shift(
        manager_id=manager.id,
        starts_at=datetime.now(timezone.utc) + timedelta(hours=1),
        ends_at=datetime.now(timezone.utc) + timedelta(hours=9),
        max_employees=3,
    )
    db_session.add(shift)
    await db_session.commit()
    await db_session.refresh(shift)
    return shift


@pytest.fixture
async def manager_task(
    db_session: AsyncSession,
    manager: User,
    employee: User,
) -> Task:
    task = Task(
        title="Manager Task",
        employee_id=employee.id,
        manager_id=manager.id,
        status=TaskStatus.TODO,
    )
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)
    return task


@pytest.mark.asyncio
async def test_team_stats_shows_summary(
    db_session: AsyncSession,
    manager: User,
    employee: User,
    manager_shift: Shift,
    manager_task: Task,
) -> None:
    from shift_manager_bot.bot.handlers.manager import cmd_team_stats

    tg_user = make_tg_user(manager.telegram_id)
    message = make_message(tg_user)

    await cmd_team_stats(message, manager, db_session)

    message.answer.assert_called_once()
    response_text: str = message.answer.call_args[0][0]
    assert "shift" in response_text.lower() or "task" in response_text.lower()


@pytest.mark.asyncio
async def test_team_stats_shows_correct_counts(
    db_session: AsyncSession,
    manager: User,
    employee: User,
    manager_shift: Shift,
    manager_task: Task,
) -> None:
    from shift_manager_bot.bot.handlers.manager import cmd_team_stats

    tg_user = make_tg_user(manager.telegram_id)
    message = make_message(tg_user)

    await cmd_team_stats(message, manager, db_session)

    message.answer.assert_called_once()
    response_text: str = message.answer.call_args[0][0]
    assert "1" in response_text
