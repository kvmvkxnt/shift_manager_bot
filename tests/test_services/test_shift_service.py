import random
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from shift_manager_bot.database.models.shift import (
    AssignmentStatus,
    Shift,
    ShiftAssignment,
)
from shift_manager_bot.database.models.user import User, UserRole
from shift_manager_bot.services.shift_service import ShiftService


@pytest.fixture
def service() -> ShiftService:
    return ShiftService()


@pytest.fixture
async def employee(db_session: AsyncSession) -> User:
    user = User(
        telegram_id=random.randint(1300000000, 1399999999),
        full_name="Shift Service Employee",
        role=UserRole.EMPLOYEE,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def employee2(db_session: AsyncSession) -> User:
    user = User(
        telegram_id=random.randint(1600000000, 1699999999),
        full_name="Shift Service Employee 2",
        role=UserRole.EMPLOYEE,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def manager(db_session: AsyncSession) -> User:
    user = User(
        telegram_id=random.randint(1400000000, 1499999999),
        full_name="Shift Service Manager",
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
    db_session: AsyncSession, service: ShiftService, manager: User
) -> None:
    now = datetime.now(timezone.utc)
    shift: Shift = await service.create_shift(
        db_session,
        manager_id=manager.id,
        starts_at=now + timedelta(hours=2),
        ends_at=now + timedelta(hours=10),
        max_employees=3,
    )

    assert shift.id is not None
    assert shift.manager_id == manager.id
    assert shift.max_employees == 3


@pytest.mark.asyncio
async def test_create_shift_with_note(
    db_session: AsyncSession, service: ShiftService, manager: User
) -> None:
    now = datetime.now(timezone.utc)
    shift: Shift = await service.create_shift(
        db_session,
        manager_id=manager.id,
        starts_at=now + timedelta(hours=3),
        ends_at=now + timedelta(hours=11),
        note="Please arrive 10 minutes early",
    )

    assert shift.note == "Please arrive 10 minutes early"


@pytest.mark.asyncio
async def test_get_by_id(
    db_session: AsyncSession, service: ShiftService, existing_shift: Shift
) -> None:
    shift: Shift | None = await service.get_by_id(db_session, existing_shift.id)

    assert shift is not None
    assert shift.id == existing_shift.id


@pytest.mark.asyncio
async def test_get_by_id_not_found(
    db_session: AsyncSession, service: ShiftService
) -> None:
    shift: Shift | None = await service.get_by_id(db_session, 99999)

    assert shift is None


@pytest.mark.asyncio
async def test_assign_employee(
    db_session: AsyncSession,
    service: ShiftService,
    existing_shift: Shift,
    employee: User,
) -> None:
    assignment: ShiftAssignment = await service.assign_employee(
        db_session, shift=existing_shift, employee_id=employee.id
    )
    assert assignment.id is not None
    assert assignment.shift_id == existing_shift.id
    assert assignment.employee_id == employee.id
    assert assignment.status == AssignmentStatus.PENDING


@pytest.mark.asyncio
async def test_assign_multiple_employees(
    db_session: AsyncSession,
    service: ShiftService,
    existing_shift: Shift,
    employee: User,
    employee2: User,
) -> None:
    await service.assign_employee(
        db_session, shift=existing_shift, employee_id=employee.id
    )
    await service.assign_employee(
        db_session, shift=existing_shift, employee_id=employee2.id
    )

    assignments: list[ShiftAssignment] = await service.get_shift_assignments(
        db_session, existing_shift.id
    )

    assert len(assignments) == 2


@pytest.mark.asyncio
async def test_cannot_exceed_max_employees(
    db_session: AsyncSession,
    service: ShiftService,
    manager: User,
    employee: User,
    employee2: User,
) -> None:
    now = datetime.now(timezone.utc)
    shift: Shift = await service.create_shift(
        db_session,
        manager_id=manager.id,
        starts_at=now + timedelta(hours=1),
        ends_at=now + timedelta(hours=9),
        max_employees=1,
    )
    await service.assign_employee(db_session, shift=shift, employee_id=employee.id)

    with pytest.raises(ValueError, match="maximum"):
        await service.assign_employee(db_session, shift=shift, employee_id=employee2.id)


@pytest.mark.asyncio
async def test_update_assignment_status(
    db_session: AsyncSession,
    service: ShiftService,
    existing_shift: Shift,
    employee: User,
) -> None:
    assignment: ShiftAssignment = await service.assign_employee(
        db_session, shift=existing_shift, employee_id=employee.id
    )
    updated: ShiftAssignment = await service.update_assignment_status(
        db_session, assignment=assignment, status=AssignmentStatus.CONFIRMED
    )

    assert updated.status == AssignmentStatus.CONFIRMED


@pytest.mark.asyncio
async def test_get_employee_shifts(
    db_session: AsyncSession,
    service: ShiftService,
    existing_shift: Shift,
    employee: User,
) -> None:
    await service.assign_employee(
        db_session, shift=existing_shift, employee_id=employee.id
    )

    shifts: list[Shift] = await service.get_employee_shifts(db_session, employee.id)

    assert len(shifts) >= 1
    assert any(s.id == existing_shift.id for s in shifts)


@pytest.mark.asyncio
async def test_get_manager_shifts(
    db_session: AsyncSession,
    service: ShiftService,
    existing_shift: Shift,
    manager: User,
) -> None:
    shifts: list[Shift] = await service.get_manager_shifts(db_session, manager.id)

    assert len(shifts) >= 1
    assert all(s.manager_id == manager.id for s in shifts)


@pytest.mark.asyncio
async def test_get_upcoming_shifts(
    db_session: AsyncSession, service: ShiftService, manager: User, employee: User
) -> None:
    now = datetime.now(timezone.utc)
    upcoming_shift: Shift = await service.create_shift(
        db_session,
        manager_id=manager.id,
        starts_at=now + timedelta(minutes=30),
        ends_at=now + timedelta(hours=8),
    )
    far_shift: Shift = await service.create_shift(
        db_session,
        manager_id=manager.id,
        starts_at=now + timedelta(days=5),
        ends_at=now + timedelta(days=5, hours=8),
    )

    await service.assign_employee(
        db_session, shift=upcoming_shift, employee_id=employee.id
    )
    await service.assign_employee(db_session, shift=far_shift, employee_id=employee.id)

    shifts: list[Shift] = await service.get_upcoming_shifts(db_session, within_hours=1)

    ids = [s.id for s in shifts]
    assert upcoming_shift.id in ids
    assert far_shift.id not in ids
