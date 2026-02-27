from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from shift_manager_bot.api.dependencies import get_current_user, get_db, require_role
from shift_manager_bot.database.models.task import Task, TaskStatus
from shift_manager_bot.database.models.user import User, UserRole
from shift_manager_bot.services.task_service import TaskService


router = APIRouter()


class TaskCreate(BaseModel):
    title: str
    employee_id: int
    description: str | None = None
    deadline: datetime | None = None


class UpdateTaskStatusRequest(BaseModel):
    status: TaskStatus


class TaskResponse(BaseModel):
    id: int
    title: str
    description: str | None
    employee_id: int
    manager_id: int
    deadline: datetime | None
    status: TaskStatus
    created_at: datetime

    model_config = {"from_attributes": True}


@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    body: TaskCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.MANAGER, UserRole.OWNER)),
) -> Task:
    service = TaskService()
    return await service.create_task(
        session,
        title=body.title,
        employee_id=body.employee_id,
        manager_id=current_user.id,
        description=body.description,
        deadline=body.deadline,
    )


@router.get("/my", response_model=list[TaskResponse])
async def get_my_tasks(
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Task]:
    service = TaskService()
    if current_user.role in (UserRole.MANAGER, UserRole.OWNER):
        return await service.get_manager_tasks(session, current_user.id)
    return await service.get_employee_tasks(session, current_user.id)


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: int,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Task:
    service = TaskService()
    task = await service.get_by_id(session, task_id)
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )
    return task


@router.patch("/{task_id}/status", response_model=TaskResponse)
async def update_task_status(
    task_id: int,
    body: UpdateTaskStatusRequest,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Task:
    service = TaskService()
    task = await service.get_by_id(session, task_id)
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )
    return await service.update_status(session, task, body.status)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: int,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.MANAGER, UserRole.OWNER)),
) -> None:
    service = TaskService()
    task = await service.get_by_id(session, task_id)
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )
    await service.delete_task(session, task)
