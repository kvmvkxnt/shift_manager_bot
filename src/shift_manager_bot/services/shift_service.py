from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shift_manager_bot.database.models.shift import (
    AssignmentStatus,
    Shift,
    ShiftAssignment,
)


class ShiftService:
    async def create_shift(
        self,
        session: AsyncSession,
        manager_id: int,
        starts_at: datetime,
        ends_at: datetime,
        max_employees: int = 1,
        note: str | None = None,
    ) -> Shift:
        shift = Shift(
            manager_id=manager_id,
            starts_at=starts_at,
            ends_at=ends_at,
            max_employees=max_employees,
            note=note,
        )
        session.add(shift)
        await session.commit()
        await session.refresh(shift)
        return shift

    async def get_by_id(self, session: AsyncSession, shift_id: int) -> Shift | None:
        result = await session.execute(select(Shift).where(Shift.id == shift_id))
        return result.scalar_one_or_none()

    async def assign_employee(
        self, session: AsyncSession, shift: Shift, employee_id: int
    ) -> ShiftAssignment:
        assignments = await self.get_shift_assignments(session, shift.id)
        if len(assignments) >= shift.max_employees:
            raise ValueError(
                f"Shift has reached maximum number of employees ({shift.max_employees})"
            )

        assignment = ShiftAssignment(shift_id=shift.id, employee_id=employee_id)
        session.add(assignment)
        await session.commit()
        await session.refresh(assignment)
        return assignment

    async def get_shift_assignments(
        self, session: AsyncSession, shift_id: int
    ) -> list[ShiftAssignment]:
        result = await session.execute(
            select(ShiftAssignment).where(ShiftAssignment.shift_id == shift_id)
        )
        return list(result.scalars().all())

    async def update_assignment_status(
        self,
        session: AsyncSession,
        assignment: ShiftAssignment,
        status: AssignmentStatus,
    ) -> ShiftAssignment:
        assignment.status = status
        await session.commit()
        await session.refresh(assignment)
        return assignment

    async def get_employee_shifts(
        self, session: AsyncSession, employee_id: int
    ) -> list[Shift]:
        result = await session.execute(
            select(Shift)
            .join(ShiftAssignment, ShiftAssignment.shift_id == Shift.id)
            .where(ShiftAssignment.employee_id == employee_id)
        )
        return list(result.scalars().all())

    async def get_manager_shifts(
        self, session: AsyncSession, manager_id: int
    ) -> list[Shift]:
        result = await session.execute(
            select(Shift).where(Shift.manager_id == manager_id)
        )
        return list(result.scalars().all())

    async def get_upcoming_shifts(
        self, session: AsyncSession, within_hours: int
    ) -> list[Shift]:
        now = datetime.now(timezone.utc)
        deadline = now + timedelta(hours=within_hours)
        result = await session.execute(
            select(Shift).where(Shift.starts_at >= now, Shift.starts_at <= deadline)
        )
        return list(result.scalars().all())
