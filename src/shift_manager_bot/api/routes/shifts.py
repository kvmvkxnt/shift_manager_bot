from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from shift_manager_bot.api.dependencies import get_current_user, get_db, require_role
from shift_manager_bot.database.models.shift import (
    AssignmentStatus,
    Shift,
    ShiftAssignment,
)
from shift_manager_bot.database.models.user import User, UserRole
from shift_manager_bot.services.shift_service import ShiftService

router = APIRouter()


class ShiftCreate(BaseModel):
    starts_at: datetime
    ends_at: datetime
    max_employees: int = 1
    note: str | None = None


class AssignEmployeeRequest(BaseModel):
    employee_id: int


class UpdateAssignmentStatusRequest(BaseModel):
    status: AssignmentStatus


class ShiftResponse(BaseModel):
    id: int
    manager_id: int
    starts_at: datetime
    ends_at: datetime
    max_employees: int
    note: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class AssignmentResponse(BaseModel):
    id: int
    shift_id: int
    employee_id: int
    status: AssignmentStatus

    model_config = {"from_attributes": True}


@router.post("/", response_model=ShiftResponse, status_code=status.HTTP_201_CREATED)
async def create_shift(
    body: ShiftCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.MANAGER, UserRole.OWNER)),
) -> Shift:
    service = ShiftService()
    return await service.create_shift(
        session,
        manager_id=current_user.id,
        starts_at=body.starts_at,
        ends_at=body.ends_at,
        max_employees=body.max_employees,
        note=body.note,
    )


@router.get("/my", response_model=list[ShiftResponse])
async def get_my_shifts(
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Shift]:
    service = ShiftService()
    if current_user.role in (UserRole.MANAGER, UserRole.OWNER):
        return await service.get_manager_shifts(session, current_user.id)
    return await service.get_employee_shifts(session, current_user.id)


@router.get("/{shift_id}", response_model=ShiftResponse)
async def get_shift(
    shift_id: int,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Shift:
    service = ShiftService()
    shift = await service.get_by_id(session, shift_id)
    if shift is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Shift not found"
        )
    return shift


@router.post(
    "/{shift_id}/assign",
    response_model=AssignmentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def assign_employee(
    shift_id: int,
    body: AssignEmployeeRequest,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.MANAGER, UserRole.OWNER)),
) -> ShiftAssignment:
    service = ShiftService()
    shift = await service.get_by_id(session, shift_id)
    if shift is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Shift not found"
        )

    try:
        return await service.assign_employee(
            session, shift=shift, employee_id=body.employee_id
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.patch("/assignments/{assignment_id}", response_model=AssignmentResponse)
async def update_assignment_status(
    assignment_id: int,
    body: UpdateAssignmentStatusRequest,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ShiftAssignment:
    service = ShiftService()
    result = await session.get(ShiftAssignment, assignment_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found"
        )
    return await service.update_assignment_status(
        session, assignment=result, status=body.status
    )
