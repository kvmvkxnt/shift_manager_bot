from datetime import datetime, timedelta, timezone
from typing import Any

from aiogram import Bot
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from shift_manager_bot.database.models.shift import (
    AssignmentStatus,
    Shift,
    ShiftAssignment,
)


async def send_shift_reminders(bot: Bot, session: AsyncSession) -> None:
    now = datetime.now(timezone.utc)
    within_one_hour = now + timedelta(hours=1)

    result = await session.execute(
        select(ShiftAssignment)
        .join(Shift)
        .where(
            Shift.starts_at >= now,
            Shift.starts_at <= within_one_hour,
            ShiftAssignment.status == AssignmentStatus.CONFIRMED,
        )
        .options(
            selectinload(ShiftAssignment.shift), selectinload(ShiftAssignment.employee)
        )
    )
    assignments = list(result.scalars().all())

    for assignment in assignments:
        shift = assignment.shift
        employee = assignment.employee
        time_str = shift.starts_at.strftime("%H:%M")
        date_str = shift.starts_at.strftime("%Y-%m-%d")

        await bot.send_message(
            employee.telegram_id,
            f"Shift reminder!¬¬"
            f"Your shift #{shift.id} starts soon.¬"
            f"Date: {date_str}¬"
            f"Time: {time_str}¬" + (f"Note: {shift.note}" if shift.note else ""),
        )
