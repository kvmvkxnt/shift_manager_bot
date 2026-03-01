import random
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from shift_manager_bot.database.models.task import Task, TaskStatus
from shift_manager_bot.database.models.user import User, UserRole
from shift_manager_bot.services.task_service import TaskService


@pytest.fixture
def service() -> TaskService:
    return TaskService()


@pytest.fixture
async def employee(db_session: AsyncSession) -> User:
    user = User(
        telegram_id=random.randint(1700000000, 1799999999),
        full_name="Shift Service Employee",
        role=UserRole.EMPLOYEE,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def manager(db_session: AsyncSession) -> User:
    user = User(
        telegram_id=random.randint(1800000000, 1899999999),
        full_name="Shift Service Manager",
        role=UserRole.MANAGER,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def existing_task(
    db_session: AsyncSession, employee: User, manager: User
) -> Task:
    task = Task(title="Existing Task", employee_id=employee.id, manager_id=manager.id)
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)
    return task


@pytest.mark.asyncio
async def test_create_task_minimal(
    db_session: AsyncSession, service: TaskService, employee: User, manager: User
) -> None:
    task: Task = await service.create_task(
        db_session,
        title="Clean Tasbles",
        employee_id=employee.id,
        manager_id=manager.id,
    )

    assert task.id is not None
    assert task.title == "Clean Tasbles"
    assert task.status == TaskStatus.TODO
    assert task.description is None
    assert task.deadline is None
    assert task.created_at is not None


@pytest.mark.asyncio
async def test_create_task_all_fields(
    db_session: AsyncSession, service: TaskService, employee: User, manager: User
) -> None:
    deadline = datetime.now(timezone.utc) + timedelta(hours=5)
    task: Task = await service.create_task(
        db_session,
        title="Full Task",
        employee_id=employee.id,
        manager_id=manager.id,
        description="Do everything",
        deadline=deadline,
    )

    assert task.description == "Do everything"
    assert task.deadline is not None


@pytest.mark.asyncio
async def test_get_by_id(
    db_session: AsyncSession, service: TaskService, existing_task: Task
) -> None:
    task: Task | None = await service.get_by_id(db_session, existing_task.id)

    assert task is not None
    assert task.id == existing_task.id


@pytest.mark.asyncio
async def test_get_by_id_not_found(
    db_session: AsyncSession, service: TaskService
) -> None:
    task: Task | None = await service.get_by_id(db_session, 999999999)

    assert task is None


@pytest.mark.asyncio
async def test_get_employee_tasks(
    db_session: AsyncSession, service: TaskService, employee: User, manager: User
) -> None:
    task1 = Task(title="Task 1", employee_id=employee.id, manager_id=manager.id)
    task2 = Task(title="Task 2", employee_id=employee.id, manager_id=manager.id)
    db_session.add_all([task1, task2])
    await db_session.commit()

    tasks: list[Task] = await service.get_employee_tasks(db_session, employee.id)
    assert len(tasks) >= 2
    assert all(task.employee_id == employee.id for task in tasks)


@pytest.mark.asyncio
async def test_get_manager_tasks(
    db_session: AsyncSession, service: TaskService, existing_task: Task, manager: User
) -> None:
    tasks: list[Task] = await service.get_manager_tasks(db_session, manager.id)

    assert len(tasks) >= 1
    assert all(task.manager_id == manager.id for task in tasks)


@pytest.mark.asyncio
async def test_update_status(
    db_session: AsyncSession, service: TaskService, existing_task: Task
) -> None:
    updated: Task = await service.update_status(
        db_session, existing_task, TaskStatus.IN_PROGRESS
    )

    assert updated.status == TaskStatus.IN_PROGRESS


@pytest.mark.asyncio
async def test_update_deadline(
    db_session: AsyncSession, service: TaskService, existing_task: Task
) -> None:
    new_deadline = datetime.now(timezone.utc) + timedelta(days=2)
    updated: Task = await service.update_deadline(
        db_session, existing_task, new_deadline
    )

    assert updated.deadline is not None


@pytest.mark.asyncio
async def test_remove_deadline(
    db_session: AsyncSession, service: TaskService, existing_task: Task
) -> None:
    updated: Task = await service.update_deadline(db_session, existing_task, None)

    assert updated.deadline is None


@pytest.mark.asyncio
async def test_delete_task(
    db_session: AsyncSession, service: TaskService, existing_task: Task
) -> None:
    task_id: int = existing_task.id
    await service.delete_task(db_session, existing_task)

    deleted: Task | None = await service.get_by_id(db_session, task_id)
    assert deleted is None
