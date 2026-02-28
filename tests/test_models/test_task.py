import random
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shift_manager_bot.database.models.task import Task, TaskStatus
from shift_manager_bot.database.models.user import User, UserRole


@pytest.fixture
async def employee(db_session: AsyncSession) -> User:
    user = User(
        telegram_id=random.randint(600000000, 699999999),
        full_name="Task Employee",
        role=UserRole.EMPLOYEE,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def manager(db_session: AsyncSession) -> User:
    user = User(
        telegram_id=random.randint(700000000, 799999999),
        full_name="Task Manager",
        role=UserRole.MANAGER,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.mark.asyncio
async def test_create_task(db_session: AsyncSession, employee: User, manager: User):
    task = Task(
        title="Clean tables",
        description="Clean all tables before opening",
        employee_id=employee.id,
        manager_id=manager.id,
        deadline=datetime.now(timezone.utc) + timedelta(hours=5),
    )
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)

    assert task.id is not None
    assert task.title == "Clean tables"
    assert task.status == TaskStatus.TODO
    assert task.created_at is not None


@pytest.mark.asyncio
async def test_task_description_is_optional(
    db_session: AsyncSession, employee: User, manager: User
):
    task = Task(title="Quick task", employee_id=employee.id, manager_id=manager.id)
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)

    assert task.description is None


@pytest.mark.asyncio
async def test_task_deadline_is_optional(
    db_session: AsyncSession, employee: User, manager: User
):
    task = Task(
        title="No deadline task", employee_id=employee.id, manager_id=manager.id
    )
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)

    assert task.deadline is None


@pytest.mark.asyncio
async def test_task_status_can_be_updated(
    db_session: AsyncSession, employee: User, manager: User
):
    task = Task(title="Updatable task", employee_id=employee.id, manager_id=manager.id)
    db_session.add(task)
    await db_session.commit()

    task.status = TaskStatus.IN_PROGRESS
    await db_session.commit()
    await db_session.refresh(task)

    assert task.status == TaskStatus.IN_PROGRESS


@pytest.mark.asyncio
async def test_get_tasks_by_employee(
    db_session: AsyncSession, employee: User, manager: User
):
    task1 = Task(title="Task 1", employee_id=employee.id, manager_id=manager.id)
    task2 = Task(title="Task 2", employee_id=employee.id, manager_id=manager.id)
    db_session.add_all([task1, task2])
    await db_session.commit()

    result = await db_session.execute(
        select(Task).where(Task.employee_id == employee.id)
    )
    tasks = result.scalars().all()

    assert len(tasks) >= 2
