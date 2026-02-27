from typing import AsyncGenerator
import pytest
import random
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from shift_manager_bot.database.models.user import User, UserRole
from shift_manager_bot.api.router import app
from shift_manager_bot.api.dependencies import get_current_user, get_db
from shift_manager_bot.services.task_service import TaskService


@pytest.fixture
async def mock_manager(db_session: AsyncSession) -> User:
    user = User(
        telegram_id=random.randint(2300000000, 2399999999),
        full_name="Task Manager",
        role=UserRole.MANAGER,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def mock_employee(db_session: AsyncSession) -> User:
    user = User(
        telegram_id=random.randint(2400000000, 2499999999),
        full_name="Task Employee",
        role=UserRole.EMPLOYEE,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client


@pytest.mark.asyncio
async def test_manager_can_create_task(
    client: AsyncClient,
    mock_manager: User,
    mock_employee: User,
    db_session: AsyncSession,
) -> None:
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_current_user] = lambda: mock_manager
    app.dependency_overrides[get_db] = override_get_db

    response = await client.post(
        "/api/tasks", json={"title": "Clean tables", "employee_id": mock_employee.id}
    )
    app.dependency_overrides.clear()

    assert response.status_code == 201


@pytest.mark.asyncio
async def test_employee_cannot_create_task(
    client: AsyncClient, mock_employee: User, db_session: AsyncSession
) -> None:
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_current_user] = lambda: mock_employee
    app.dependency_overrides[get_db] = override_get_db

    response = await client.post(
        "/api/tasks", json={"title": "Clean tables", "employee_id": mock_employee.id}
    )
    app.dependency_overrides.clear()

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_my_tasks_as_employee(
    client: AsyncClient, mock_employee: User, db_session: AsyncSession
) -> None:
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_current_user] = lambda: mock_employee
    app.dependency_overrides[get_db] = override_get_db

    response = await client.get("/api/tasks/my")
    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_get_task_by_id(
    client: AsyncClient,
    mock_manager: User,
    mock_employee: User,
    db_session: AsyncSession,
) -> None:
    async def override_get_db():
        yield db_session

    service = TaskService()
    task = await service.create_task(
        db_session,
        title="Test task",
        employee_id=mock_employee.id,
        manager_id=mock_manager.id,
    )

    app.dependency_overrides[get_current_user] = lambda: mock_manager
    app.dependency_overrides[get_db] = override_get_db

    response = await client.get(f"/api/tasks/{task.id}")
    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["id"] == task.id


@pytest.mark.asyncio
async def test_get_task_not_found(
    client: AsyncClient, mock_manager: User, db_session: AsyncSession
) -> None:
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_current_user] = lambda: mock_manager
    app.dependency_overrides[get_db] = override_get_db

    response = await client.get("/api/tasks/999999")
    app.dependency_overrides.clear()

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_task_status(
    client: AsyncClient,
    mock_employee: User,
    mock_manager: User,
    db_session: AsyncSession,
) -> None:
    async def override_get_db():
        yield db_session

    service = TaskService()
    task = await service.create_task(
        db_session,
        title="Updatable task",
        employee_id=mock_employee.id,
        manager_id=mock_manager.id,
    )

    app.dependency_overrides[get_current_user] = lambda: mock_employee
    app.dependency_overrides[get_db] = override_get_db

    response = await client.patch(
        f"/api/tasks/{task.id}/status", json={"status": "in_progress"}
    )
    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["status"] == "in_progress"


@pytest.mark.asyncio
async def test_manager_can_delete_task(
    client: AsyncClient,
    mock_manager: User,
    mock_employee: User,
    db_session: AsyncSession,
) -> None:
    async def override_get_db():
        yield db_session

    service = TaskService()
    task = await service.create_task(
        db_session,
        title="Deletable task",
        employee_id=mock_employee.id,
        manager_id=mock_manager.id,
    )

    app.dependency_overrides[get_current_user] = lambda: mock_manager
    app.dependency_overrides[get_db] = override_get_db

    response = await client.delete(f"/api/tasks/{task.id}")
    app.dependency_overrides.clear()

    assert response.status_code == 204


@pytest.mark.asyncio
async def test_employee_cannot_delete_task(
    client: AsyncClient,
    mock_employee: User,
    mock_manager: User,
    db_session: AsyncSession,
) -> None:
    async def override_get_db():
        yield db_session

    service = TaskService()
    task = await service.create_task(
        db_session,
        title="Protected Task",
        employee_id=mock_employee.id,
        manager_id=mock_manager.id,
    )

    app.dependency_overrides[get_current_user] = lambda: mock_employee
    app.dependency_overrides[get_db] = override_get_db

    response = await client.delete(f"/api/tasks/{task.id}")
    app.dependency_overrides.clear()

    assert response.status_code == 403
