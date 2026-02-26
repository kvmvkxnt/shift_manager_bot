from datetime import datetime, timedelta, timezone
import pytest
import random
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shift_manager_bot.database.models.shift import (
    AssignmentStatus,
    Shift,
    ShiftAssignment,
)
from shift_manager_bot.database.models.user import User, UserRole


@pytest.fixture
async def employee(db_session: AsyncSession) -> User:
    user = User(
        telegram_id=random.randint(400000000, 499999999),
        full_name="Shift employee",
        role=UserRole.EMPLOYEE,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def employee2(db_session: AsyncSession) -> User:
    user = User(
        telegram_id=random.randint(1500000000, 1599999999),
        full_name="Shift employee 2",
        role=UserRole.EMPLOYEE,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def manager(db_session: AsyncSession) -> User:
    user = User(
        telegram_id=random.randint(500000000, 599999999),
        full_name="Shift manager",
        role=UserRole.MANAGER,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def existing_shift(db_session: AsyncSession, manager: User) -> Shift:
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


@pytest.mark.asyncio
async def test_create_shift(
    db_session,
    manager: User,
) -> None:
    now = datetime.now(timezone.utc)
    shift = Shift(
        manager_id=manager.id,
        starts_at=now + timedelta(hours=1),
        ends_at=now + timedelta(hours=9),
        max_employees=5,
    )
    db_session.add(shift)
    await db_session.commit()
    await db_session.refresh(shift)

    assert shift.id is not None
    assert shift.manager_id == manager.id
    assert shift.max_employees == 5
    assert shift.created_at is not None


@pytest.mark.asyncio
async def test_shift_max_employees_defaults_to_one(
    db_session,
    manager: User,
) -> None:
    now = datetime.now(timezone.utc)
    shift = Shift(
        manager_id=manager.id,
        starts_at=now + timedelta(hours=2),
        ends_at=now + timedelta(hours=10),
    )
    db_session.add(shift)
    await db_session.commit()
    await db_session.refresh(shift)

    assert shift.max_employees == 1


@pytest.mark.asyncio
async def test_create_shift_assignment(
    db_session,
    existing_shift: Shift,
    employee: User,
) -> None:
    assignment = ShiftAssignment(
        shift_id=existing_shift.id,
        employee_id=employee.id,
    )
    db_session.add(assignment)
    await db_session.commit()
    await db_session.refresh(assignment)

    assert assignment.id is not None
    assert assignment.shift_id == existing_shift.id
    assert assignment.employee_id == employee.id
    assert assignment.status == AssignmentStatus.PENDING


@pytest.mark.asyncio
async def test_multiple_employees_per_shift(
    db_session,
    existing_shift: Shift,
    employee: User,
    employee2: User,
) -> None:
    assignment1 = ShiftAssignment(
        shift_id=existing_shift.id,
        employee_id=employee.id,
    )
    assignment2 = ShiftAssignment(
        shift_id=existing_shift.id,
        employee_id=employee2.id,
    )
    db_session.add_all([assignment1, assignment2])
    await db_session.commit()

    result = await db_session.execute(
        select(ShiftAssignment).where(ShiftAssignment.shift_id == existing_shift.id)
    )
    assignments = result.scalars().all()

    assert len(assignments) == 2


@pytest.mark.asyncio
async def test_assignment_status_can_be_updated(
    db_session,
    existing_shift: Shift,
    employee: User,
) -> None:
    assignment = ShiftAssignment(
        shift_id=existing_shift.id,
        employee_id=employee.id,
    )
    db_session.add(assignment)
    await db_session.commit()

    assignment.status = AssignmentStatus.CONFIRMED
    await db_session.commit()
    await db_session.refresh(assignment)

    assert assignment.status == AssignmentStatus.CONFIRMED


@pytest.mark.asyncio
async def test_get_assignments_by_employee(
    db_session,
    existing_shift: Shift,
    employee: User,
) -> None:
    assignment = ShiftAssignment(
        shift_id=existing_shift.id,
        employee_id=employee.id,
    )
    db_session.add(assignment)
    await db_session.commit()

    result = await db_session.execute(
        select(ShiftAssignment).where(ShiftAssignment.employee_id == employee.id)
    )
    assignments = result.scalars().all()

    assert len(assignments) >= 1
