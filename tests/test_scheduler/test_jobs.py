import random
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from shift_manager_bot.database.models.shift import (
    AssignmentStatus,
    Shift,
    ShiftAssignment,
)
from shift_manager_bot.database.models.user import User, UserRole


@pytest.fixture
async def manager(db_session: AsyncSession) -> User:
    user = User(
        telegram_id=random.randint(5000000000, 5099999999),
        full_name="Scheduler Manager",
        role=UserRole.MANAGER,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def employee(db_session: AsyncSession) -> User:
    user = User(
        telegram_id=random.randint(5100000000, 5199999999),
        full_name="Scheduler Employee",
        role=UserRole.EMPLOYEE,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def upcoming_shift(
    db_session: AsyncSession,
    manager: User,
    employee: User,
) -> tuple[Shift, ShiftAssignment]:
    shift = Shift(
        manager_id=manager.id,
        starts_at=datetime.now(timezone.utc) + timedelta(minutes=45),
        ends_at=datetime.now(timezone.utc) + timedelta(hours=9),
        max_employees=3,
    )
    db_session.add(shift)
    await db_session.commit()
    await db_session.refresh(shift)

    assignment = ShiftAssignment(
        shift_id=shift.id,
        employee_id=employee.id,
        status=AssignmentStatus.CONFIRMED,
    )
    db_session.add(assignment)
    await db_session.commit()
    await db_session.refresh(assignment)

    return shift, assignment


@pytest.fixture
async def far_future_shift(
    db_session: AsyncSession,
    manager: User,
    employee: User,
) -> tuple[Shift, ShiftAssignment]:
    shift = Shift(
        manager_id=manager.id,
        starts_at=datetime.now(timezone.utc) + timedelta(hours=24),
        ends_at=datetime.now(timezone.utc) + timedelta(hours=32),
        max_employees=3,
    )
    db_session.add(shift)
    await db_session.commit()
    await db_session.refresh(shift)

    assignment = ShiftAssignment(
        shift_id=shift.id,
        employee_id=employee.id,
        status=AssignmentStatus.CONFIRMED,
    )
    db_session.add(assignment)
    await db_session.commit()
    await db_session.refresh(assignment)

    return shift, assignment


def make_mock_bot() -> MagicMock:
    bot = MagicMock()
    bot.send_message = AsyncMock()
    return bot


@pytest.mark.asyncio
async def test_send_shift_reminders_notifies_employee(
    db_session: AsyncSession,
    employee: User,
    upcoming_shift: tuple[Shift, ShiftAssignment],
) -> None:
    from shift_manager_bot.scheduler.jobs import send_shift_reminders

    bot = make_mock_bot()
    await send_shift_reminders(bot, db_session)

    bot.send_message.assert_called_once()
    call_kwargs = bot.send_message.call_args
    assert (
        call_kwargs[0][0] == employee.telegram_id
        or call_kwargs[1].get("chat_id") == employee.telegram_id
    )


@pytest.mark.asyncio
async def test_send_shift_reminders_skips_far_future(
    db_session: AsyncSession,
    far_future_shift: tuple[Shift, ShiftAssignment],
) -> None:
    from shift_manager_bot.scheduler.jobs import send_shift_reminders

    bot = make_mock_bot()
    await send_shift_reminders(bot, db_session)

    bot.send_message.assert_not_called()


@pytest.mark.asyncio
async def test_send_shift_reminders_skips_pending_assignments(
    db_session: AsyncSession,
    manager: User,
    employee: User,
) -> None:
    from shift_manager_bot.scheduler.jobs import send_shift_reminders

    shift = Shift(
        manager_id=manager.id,
        starts_at=datetime.now(timezone.utc) + timedelta(minutes=45),
        ends_at=datetime.now(timezone.utc) + timedelta(hours=9),
        max_employees=3,
    )
    db_session.add(shift)
    await db_session.commit()
    await db_session.refresh(shift)

    assignment = ShiftAssignment(
        shift_id=shift.id,
        employee_id=employee.id,
        status=AssignmentStatus.PENDING,
    )
    db_session.add(assignment)
    await db_session.commit()

    bot = make_mock_bot()
    await send_shift_reminders(bot, db_session)

    bot.send_message.assert_not_called()


@pytest.mark.asyncio
async def test_send_shift_reminders_message_contains_shift_info(
    db_session: AsyncSession,
    employee: User,
    upcoming_shift: tuple[Shift, ShiftAssignment],
) -> None:
    from shift_manager_bot.scheduler.jobs import send_shift_reminders

    shift, _ = upcoming_shift
    bot = make_mock_bot()
    await send_shift_reminders(bot, db_session)

    bot.send_message.assert_called_once()
    call_args = bot.send_message.call_args
    message_text = (
        call_args[0][1] if len(call_args[0]) > 1 else call_args[1].get("text", "")
    )
    assert "shift" in message_text.lower() or str(shift.id) in message_text


@pytest.mark.asyncio
async def test_send_shift_reminders_multiple_employees(
    db_session: AsyncSession,
    manager: User,
) -> None:
    from shift_manager_bot.scheduler.jobs import send_shift_reminders

    employees = []
    for i in range(3):
        emp = User(
            telegram_id=random.randint(
                5200000000 + i * 1000000, 5200000000 + i * 1000000 + 999999
            ),
            full_name=f"Employee {i}",
            role=UserRole.EMPLOYEE,
        )
        db_session.add(emp)
        employees.append(emp)
    await db_session.commit()
    for emp in employees:
        await db_session.refresh(emp)

    shift = Shift(
        manager_id=manager.id,
        starts_at=datetime.now(timezone.utc) + timedelta(minutes=45),
        ends_at=datetime.now(timezone.utc) + timedelta(hours=9),
        max_employees=3,
    )
    db_session.add(shift)
    await db_session.commit()
    await db_session.refresh(shift)

    for emp in employees:
        assignment = ShiftAssignment(
            shift_id=shift.id,
            employee_id=emp.id,
            status=AssignmentStatus.CONFIRMED,
        )
        db_session.add(assignment)
    await db_session.commit()

    bot = make_mock_bot()
    await send_shift_reminders(bot, db_session)

    assert bot.send_message.call_count == 3
