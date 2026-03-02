from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from shift_manager_bot.database.models.task import Task, TaskStatus


class TaskService:
    async def create_task(
        self,
        session: AsyncSession,
        title: str,
        employee_id: int,
        manager_id: int,
        description: str | None = None,
        deadline: datetime | None = None,
    ) -> Task:
        task = Task(
            title=title,
            employee_id=employee_id,
            manager_id=manager_id,
            description=description,
            deadline=deadline,
        )
        session.add(task)
        await session.commit()
        await session.refresh(task)
        return task

    async def get_by_id(self, session: AsyncSession, task_id: int) -> Task | None:
        result = await session.execute(select(Task).where(Task.id == task_id))
        return result.scalar_one_or_none()

    async def get_employee_tasks(
        self, session: AsyncSession, employee_id: int
    ) -> list[Task]:
        result = await session.execute(
            select(Task).where(Task.employee_id == employee_id)
        )
        return list(result.scalars().all())

    async def get_manager_tasks(
        self, session: AsyncSession, manager_id: int
    ) -> list[Task]:
        result = await session.execute(
            select(Task).where(Task.manager_id == manager_id)
        )
        return list(result.scalars().all())

    async def update_status(
        self, session: AsyncSession, task: Task, new_status: TaskStatus
    ) -> Task:
        task.status = new_status
        await session.commit()
        await session.refresh(task)
        return task

    async def update_deadline(
        self, session: AsyncSession, task: Task, new_deadline: datetime | None
    ) -> Task:
        task.deadline = new_deadline
        await session.commit()
        await session.refresh(task)
        return task

    async def delete_task(self, session: AsyncSession, task: Task) -> None:
        await session.delete(task)
        await session.commit()

    async def get_employee_tasks_count_by_status(
        self, session: AsyncSession, employee_id: int, status: TaskStatus
    ) -> int:
        result = await session.execute(
            select(func.count(Task.id)).where(
                Task.employee_id == employee_id, Task.status == status
            )
        )
        return result.scalar_one()

    async def get_manager_tasks_count_by_status(
        self, session: AsyncSession, manager_id: int, status: TaskStatus
    ) -> int:
        result = await session.execute(
            select(func.count(Task.id)).where(
                Task.manager_id == manager_id, Task.status == status
            )
        )
        return result.scalar_one()
