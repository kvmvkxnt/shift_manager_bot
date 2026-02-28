from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shift_manager_bot.database.base import Base
from shift_manager_bot.database.models.user import User


class AssignmentStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    DECLINED = "declined"
    COMPLETED = "completed"


class Shift(Base):
    __tablename__ = "shifts"

    id: Mapped[int] = mapped_column(primary_key=True)
    manager_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    max_employees: Mapped[int] = mapped_column(
        Integer, default=1, server_default="1", nullable=False
    )
    note: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    manager: Mapped["User"] = relationship(foreign_keys=[manager_id])
    assignments: Mapped[list["ShiftAssignment"]] = relationship(
        back_populates="shift", cascade="all, delete-orphan"
    )


class ShiftAssignment(Base):
    __tablename__ = "shift_assignments"

    id: Mapped[int] = mapped_column(primary_key=True)
    shift_id: Mapped[int] = mapped_column(
        ForeignKey("shifts.id", ondelete="CASCADE"), nullable=False
    )
    employee_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[AssignmentStatus] = mapped_column(
        SqlEnum(AssignmentStatus, name="assignmentstatus", create_type=True),
        default=AssignmentStatus.PENDING,
        nullable=False,
    )

    shift: Mapped["Shift"] = relationship(back_populates="assignments")
    employee: Mapped["User"] = relationship(foreign_keys=[employee_id])
