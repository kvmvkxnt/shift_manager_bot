from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from shift_manager_bot.database.models.invite_code import InviteCode
from shift_manager_bot.database.models.user import UserRole


class InviteCodeService:
    async def generate(
        self,
        session: AsyncSession,
        role: UserRole,
        created_by: int,
        manager_id: int | None = None,
        expires_at: datetime | None = None,
    ) -> InviteCode:
        pass

    async def get_by_code(self, session: AsyncSession, code: str) -> InviteCode | None:
        pass

    async def validate(
        self, session: AsyncSession, code: str
    ) -> tuple[bool, Exception | None]:
        pass

    async def redeem(
        self, session: AsyncSession, invite_code: InviteCode, employee_id: int
    ) -> InviteCode:
        pass
