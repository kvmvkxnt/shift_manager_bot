import random
from datetime import datetime, timedelta, timezone
from typing import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient

from shift_manager_bot.api.dependencies import get_current_user, get_db
from shift_manager_bot.api.router import app
from shift_manager_bot.database.models.shift import (
    AssignmentStatus,
    Shift,
    ShiftAssignment,
)
from shift_manager_bot.database.models.user import User, UserRole
from shift_manager_bot.services.shift_service import ShiftService


@pytest.fixture
async def mock_manager(db_session) -> User:
    user = User(
        telegram_id=random.randint(2100000000, 2199999999),
        full_name="Test Manager",
        role=UserRole.MANAGER,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def mock_employee(db_session) -> User:
    user = User(
        telegram_id=random.randint(2200000000, 2299999999),
        full_name="Test Employee",
        role=UserRole.EMPLOYEE,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client


@pytest.mark.asyncio
async def test_manager_can_create_shift(
    client: AsyncClient,
    mock_manager: User,
    db_session,
) -> None:
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_current_user] = lambda: mock_manager
    app.dependency_overrides[get_db] = override_get_db
    response = await client.post(
        "/api/shifts/",
        json={
            "starts_at": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
            "ends_at": (datetime.now(timezone.utc) + timedelta(hours=9)).isoformat(),
            "max_employees": 3,
        },
    )
    app.dependency_overrides.clear()

    assert response.status_code == 201


@pytest.mark.asyncio
async def test_employee_cannot_create_shift(
    client: AsyncClient,
    mock_employee: User,
    db_session,
) -> None:
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_current_user] = lambda: mock_employee
    app.dependency_overrides[get_db] = override_get_db
    response = await client.post(
        "/api/shifts/",
        json={
            "starts_at": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
            "ends_at": (datetime.now(timezone.utc) + timedelta(hours=9)).isoformat(),
            "max_employees": 2,
        },
    )
    app.dependency_overrides.clear()

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_my_shifts_as_employee(
    client: AsyncClient,
    mock_employee: User,
    db_session,
) -> None:
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_current_user] = lambda: mock_employee
    app.dependency_overrides[get_db] = override_get_db
    response = await client.get("/api/shifts/my")
    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_get_shift_by_id(
    client: AsyncClient,
    mock_manager: User,
    db_session,
) -> None:
    async def override_get_db():
        yield db_session

    service = ShiftService()
    shift = await service.create_shift(
        db_session,
        manager_id=mock_manager.id,
        starts_at=datetime.now(timezone.utc) + timedelta(hours=1),
        ends_at=datetime.now(timezone.utc) + timedelta(hours=9),
    )

    app.dependency_overrides[get_current_user] = lambda: mock_manager
    app.dependency_overrides[get_db] = override_get_db
    response = await client.get(f"/api/shifts/{shift.id}")
    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["id"] == shift.id


@pytest.mark.asyncio
async def test_get_shift_not_found(
    client: AsyncClient,
    mock_manager: User,
    db_session,
) -> None:
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_current_user] = lambda: mock_manager
    app.dependency_overrides[get_db] = override_get_db
    response = await client.get("/api/shifts/999999")
    app.dependency_overrides.clear()

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_assign_employee_to_shift(
    client: AsyncClient,
    mock_manager: User,
    mock_employee: User,
    db_session,
) -> None:
    async def override_get_db():
        yield db_session

    service = ShiftService()
    shift = await service.create_shift(
        db_session,
        manager_id=mock_manager.id,
        starts_at=datetime.now(timezone.utc) + timedelta(hours=1),
        ends_at=datetime.now(timezone.utc) + timedelta(hours=9),
        max_employees=3,
    )

    app.dependency_overrides[get_current_user] = lambda: mock_manager
    app.dependency_overrides[get_db] = override_get_db
    response = await client.post(
        f"/api/shifts/{shift.id}/assign",
        json={"employee_id": mock_employee.id},
    )
    app.dependency_overrides.clear()

    assert response.status_code == 201


@pytest.mark.asyncio
async def test_update_assignment_status(
    client: AsyncClient,
    mock_employee: User,
    mock_manager: User,
    db_session,
) -> None:
    async def override_get_db():
        yield db_session

    service = ShiftService()
    shift = await service.create_shift(
        db_session,
        manager_id=mock_manager.id,
        starts_at=datetime.now(timezone.utc) + timedelta(hours=1),
        ends_at=datetime.now(timezone.utc) + timedelta(hours=9),
    )
    assignment = await service.assign_employee(
        db_session,
        shift=shift,
        employee_id=mock_employee.id,
    )

    app.dependency_overrides[get_current_user] = lambda: mock_employee
    app.dependency_overrides[get_db] = override_get_db
    response = await client.patch(
        f"/api/shifts/assignments/{assignment.id}",
        json={"status": "confirmed"},
    )
    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["status"] == "confirmed"
