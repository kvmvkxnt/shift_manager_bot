import random
from typing import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from shift_manager_bot.api.dependencies import get_current_user, get_db
from shift_manager_bot.api.router import app
from shift_manager_bot.database.models.user import User, UserRole


def make_mock_user(role: UserRole = UserRole.EMPLOYEE) -> User:
    user = User(
        telegram_id=random.randint(20000000000, 20999999999),
        full_name="Test User",
        username="testuser",
        role=role,
    )
    user.id = 1
    user.is_active = True
    return user


@pytest.fixture
def mock_employee() -> User:
    return make_mock_user(UserRole.EMPLOYEE)


@pytest.fixture
def mock_manager() -> User:
    return make_mock_user(UserRole.MANAGER)


@pytest.fixture
def mock_owner() -> User:
    return make_mock_user(UserRole.OWNER)


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client


@pytest.mark.asyncio
async def test_get_me(client: AsyncClient, mock_employee: User) -> None:
    app.dependency_overrides[get_current_user] = lambda: mock_employee
    response = await client.get("/api/users/me")
    app.dependency_overrides.clear()

    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == mock_employee.full_name
    assert data["role"] == mock_employee.role.value


@pytest.mark.asyncio
async def test_get_me_unauthorized(client: AsyncClient) -> None:
    response = await client.get("/api/users/me")
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_manager_can_list_team(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    async def override_get_db():
        yield db_session

    manager = User(
        telegram_id=random.randint(2400000000, 2499999999),
        full_name="Test Manager",
        role=UserRole.MANAGER,
    )
    db_session.add(manager)
    await db_session.commit()
    await db_session.refresh(manager)

    employee = User(
        telegram_id=random.randint(2500000000, 2599999999),
        full_name="Team Employee",
        role=UserRole.EMPLOYEE,
        manager_id=manager.id,
    )
    db_session.add(employee)
    await db_session.commit()
    await db_session.refresh(employee)

    app.dependency_overrides[get_current_user] = lambda: manager
    app.dependency_overrides[get_db] = override_get_db
    response = await client.get("/api/users/team")
    app.dependency_overrides.clear()

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert any(u["id"] == employee.id for u in data)


@pytest.mark.asyncio
async def test_employee_cannot_list_team(
    client: AsyncClient, mock_employee: User
) -> None:
    app.dependency_overrides[get_current_user] = lambda: mock_employee
    response = await client.get("/api/users/team")
    app.dependency_overrides.clear()

    assert response.status_code == 403
