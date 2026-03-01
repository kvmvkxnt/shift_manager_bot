from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, String, func, Enum as SqlEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from shift_manager_bot.database.base import Base
from shift_manager_bot.database.models.user import User, UserRole


class InviteCode(Base):
    __tablename__ = "invite_codes"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    role: Mapped[UserRole] = mapped_column(
        SqlEnum(UserRole, name="userrole", create_type=False), nullable=False
    )
    manager_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_by: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    used_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    manager: Mapped["User | None"] = relationship(foreign_keys=[manager_id])
    creator: Mapped["User"] = relationship(foreign_keys=[created_by])
    user: Mapped["User | None"] = relationship(foreign_keys=[used_by])
