import random
from datetime import datetime, timedelta, timezone
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram.types import CallbackQuery, Message
from aiogram.types import User as TgUser
from sqlalchemy.ext.asyncio import AsyncSession

from shift_manager_bot.bot.callbacks import ShiftCallbackData, TaskCallbackData
from shift_manager_bot.database.models.shift import (
    AssignmentStatus,
    Shift,
    ShiftAssignment,
)
from shift_manager_bot.database.models.task import Task, TaskStatus
from shift_manager_bot.database.models.user import User, UserRole


def make_tg_user(user_id: int) -> TgUser:
    return TgUser(id=user_id, is_bot=False, first_name="Test", username="testuser")


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
    return callback


@pytest.fixture
async def employee(db_session: AsyncSession) -> User:
    user = User(
        telegram_id=random.randint(3500000000, 3599999999),
        full_name="Employee",
        role=UserRole.EMPLOYEE,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def manager(db_session: AsyncSession) -> User:
    user = User(
        telegram_id=random.randint(3600000000, 3699999999),
        full_name="Manager",
        role=UserRole.MANAGER,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def shift_with_assignment(
    db_session: AsyncSession, employee: User, manager: User
) -> tuple[Shift, ShiftAssignment]:
    shift = Shift(
        manager_id=manager.id,
        starts_at=datetime.now(timezone.utc) + timedelta(hours=2),
        ends_at=datetime.now(timezone.utc) + timedelta(hours=10),
        max_employees=3,
    )
    db_session.add(shift)
    await db_session.commit()
    await db_session.refresh(shift)

    assignment = ShiftAssignment(
        shift_id=shift.id, employee_id=employee.id, status=AssignmentStatus.PENDING
    )
    db_session.add(assignment)
    await db_session.commit()
    await db_session.refresh(assignment)

    return shift, assignment


@pytest.fixture
async def employee_task(
    db_session: AsyncSession, employee: User, manager: User
) -> Task:
    task = Task(
        title="Test Task",
        employee_id=employee.id,
        manager_id=manager.id,
        status=TaskStatus.TODO,
    )
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)
    return task


# /my_shifts tests
@pytest.mark.asyncio
async def test_my_shifts_shows_shifts(
    db_session: AsyncSession,
    employee: User,
    shift_with_assignment: tuple[Shift, ShiftAssignment],
) -> None:
    from shift_manager_bot.bot.handlers.employee import cmd_my_shifts

    tg_user = make_tg_user(employee.telegram_id)
    message = make_message(tg_user)
    data: dict[str, Any] = {"session": db_session, "user": employee}

    await cmd_my_shifts(message, data)

    shift, _ = shift_with_assignment
    message.answer.assert_called_once()
    response_text: str = message.answer.call_args[0][0]
    assert str(shift.id) in response_text


@pytest.mark.asyncio
async def test_my_shifts_empty(db_session: AsyncSession, employee: User) -> None:
    from shift_manager_bot.bot.handlers.employee import cmd_my_shifts

    tg_user = make_tg_user(employee.telegram_id)
    message = make_message(tg_user)
    data: dict[str, Any] = {"session": db_session, "user": employee}

    await cmd_my_shifts(message, data)

    message.answer.assert_called_once()
    response_text: str = message.answer.call_args[0][0]
    assert "no" in response_text.lower() or "empty" in response_text.lower()


@pytest.mark.asyncio
async def test_confirm_shift(
    db_session: AsyncSession,
    employee: User,
    shift_with_assignment: tuple[Shift, ShiftAssignment],
) -> None:
    from shift_manager_bot.bot.handlers.employee import on_shift_action

    _, assignment = shift_with_assignment
    tg_user = make_tg_user(employee.telegram_id)
    callback = make_callback(tg_user)
    callback_data = ShiftCallbackData(action="confirm", assignment_id=assignment.id)
    data: dict[str, Any] = {"session": db_session, "user": employee}

    await on_shift_action(callback, callback_data, data)

    await db_session.refresh(assignment)
    assert assignment.status == AssignmentStatus.CONFIRMED
    callback.answer.assert_called_once()


@pytest.mark.asyncio
async def test_decline_shift(
    db_session: AsyncSession,
    employee: User,
    shift_with_assignment: tuple[Shift, ShiftAssignment],
) -> None:
    from shift_manager_bot.bot.handlers.employee import on_shift_action

    _, assignment = shift_with_assignment
    tg_user = make_tg_user(employee.telegram_id)
    callback = make_callback(tg_user)
    callback_data = ShiftCallbackData(action="decline", assignment_id=assignment.id)
    data: dict[str, Any] = {"session": db_session, "user": employee}

    await on_shift_action(callback, callback_data, data)

    await db_session.refresh(assignment)
    assert assignment.status == AssignmentStatus.DECLINED
    callback.answer.assert_called_once()


# /my_tasks tests
@pytest.mark.asyncio
async def test_my_tasks_shows_tasks(
    db_session: AsyncSession,
    employee: User,
    employee_task: Task,
) -> None:
    from shift_manager_bot.bot.handlers.employee import cmd_my_tasks

    tg_user = make_tg_user(employee.telegram_id)
    message = make_message(tg_user)
    data: dict[str, Any] = {"session": db_session, "user": employee}

    await cmd_my_tasks(message, data)

    message.answer.assert_called_once()
    response_text: str = message.answer.call_args[0][0]
    assert employee_task.title in response_text


@pytest.mark.asyncio
async def test_my_tasks_empty(
    db_session: AsyncSession,
    employee: User,
) -> None:
    from shift_manager_bot.bot.handlers.employee import cmd_my_tasks

    tg_user = make_tg_user(employee.telegram_id)
    message = make_message(tg_user)
    data: dict[str, Any] = {"session": db_session, "user": employee}

    await cmd_my_tasks(message, data)

    message.answer.assert_called_once()
    response_text: str = message.answer.call_args[0][0]
    assert "no" in response_text.lower() or "empty" in response_text.lower()


@pytest.mark.asyncio
async def test_update_task_status_to_in_progress(
    db_session: AsyncSession,
    employee: User,
    employee_task: Task,
) -> None:
    from shift_manager_bot.bot.handlers.employee import on_task_action

    tg_user = make_tg_user(employee.telegram_id)
    callback = make_callback(tg_user)
    callback_data = TaskCallbackData(action="in_progress", task_id=employee_task.id)
    data: dict[str, Any] = {"session": db_session, "user": employee}

    await on_task_action(callback, callback_data, data)

    await db_session.refresh(employee_task)
    assert employee_task.status == TaskStatus.IN_PROGRESS
    callback.answer.assert_called_once()


@pytest.mark.asyncio
async def test_update_task_status_to_done(
    db_session: AsyncSession,
    employee: User,
    employee_task: Task,
) -> None:
    from shift_manager_bot.bot.handlers.employee import on_task_action

    tg_user = make_tg_user(employee.telegram_id)
    callback = make_callback(tg_user)
    callback_data = TaskCallbackData(action="done", task_id=employee_task.id)
    data: dict[str, Any] = {"session": db_session, "user": employee}

    await on_task_action(callback, callback_data, data)

    await db_session.refresh(employee_task)
    assert employee_task.status == TaskStatus.DONE
    callback.answer.assert_called_once()


# tests for employee stats
@pytest.fixture
async def completed_shift(
    db_session: AsyncSession,
    employee: User,
    manager: User,
) -> ShiftAssignment:
    shift = Shift(
        manager_id=manager.id,
        starts_at=datetime.now(timezone.utc) - timedelta(hours=10),
        ends_at=datetime.now(timezone.utc) - timedelta(hours=2),
        max_employees=3,
    )
    db_session.add(shift)
    await db_session.commit()
    await db_session.refresh(shift)

    assignment = ShiftAssignment(
        shift_id=shift.id,
        employee_id=employee.id,
        status=AssignmentStatus.COMPLETED,
    )
    db_session.add(assignment)
    await db_session.commit()
    await db_session.refresh(assignment)
    return assignment


@pytest.fixture
async def done_task(
    db_session: AsyncSession,
    employee: User,
    manager: User,
) -> Task:
    task = Task(
        title="Done Task",
        employee_id=employee.id,
        manager_id=manager.id,
        status=TaskStatus.DONE,
    )
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)
    return task


@pytest.mark.asyncio
async def test_my_stats_shows_summary(
    db_session: AsyncSession,
    employee: User,
    shift_with_assignment: tuple[Shift, ShiftAssignment],
    completed_shift: ShiftAssignment,
    done_task: Task,
    employee_task: Task,
) -> None:
    from shift_manager_bot.bot.handlers.employee import cmd_my_stats

    tg_user = make_tg_user(employee.telegram_id)
    message = make_message(tg_user)
    data: dict[str, Any] = {"session": db_session, "user": employee}

    await cmd_my_stats(message, data)

    message.answer.assert_called_once()
    response_text: str = message.answer.call_args[0][0]
    assert "shift" in response_text.lower() or "task" in response_text.lower()


@pytest.mark.asyncio
async def test_my_stats_shows_correct_counts(
    db_session: AsyncSession,
    employee: User,
    completed_shift: ShiftAssignment,
    done_task: Task,
) -> None:
    from shift_manager_bot.bot.handlers.employee import cmd_my_stats

    tg_user = make_tg_user(employee.telegram_id)
    message = make_message(tg_user)
    data: dict[str, Any] = {"session": db_session, "user": employee}

    await cmd_my_stats(message, data)

    message.answer.assert_called_once()
    response_text: str = message.answer.call_args[0][0]
    assert "1" in response_text
