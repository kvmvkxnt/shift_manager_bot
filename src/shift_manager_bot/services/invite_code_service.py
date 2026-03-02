import random
import string
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shift_manager_bot.database.models.invite_code import InviteCode
from shift_manager_bot.database.models.user import UserRole


class InviteCodeService:
    def _generate_code(self, length: int = 8) -> str:
        return "".join(random.choices(string.ascii_uppercase + string.digits, k=length))

    async def generate(
        self,
        session: AsyncSession,
        role: UserRole,
        created_by: int,
        manager_id: int | None = None,
        expires_at: datetime | None = None,
    ) -> InviteCode:
        while True:
            code_str = self._generate_code()
            existing = await self.get_by_code(session, code_str)
            if existing is None:
                break

        code = InviteCode(
            code=code_str,
            role=role,
            created_by=created_by,
            manager_id=manager_id,
            expires_at=expires_at,
        )
        session.add(code)
        await session.commit()
        await session.refresh(code)
        return code

    async def get_by_code(self, session: AsyncSession, code: str) -> InviteCode | None:
        result = await session.execute(
            select(InviteCode).where(InviteCode.code == code)
        )
        return result.scalar_one_or_none()

    async def validate(
        self, session: AsyncSession, code: str
    ) -> tuple[bool, str | None]:
        invite = await self.get_by_code(session, code)

        if invite is None:
            return False, "Invite code does not exist."

        if invite.used_by is not None:
            return False, "Invite code has already been used."

        if invite.expires_at is not None:
            if datetime.now(timezone.utc) > invite.expires_at:
                return False, "Invite code has expired."

        return True, None

    async def redeem(
        self, session: AsyncSession, invite_code: InviteCode, user_id: int
    ) -> InviteCode:
        invite_code.used_by = user_id
        await session.commit()
        await session.refresh(invite_code)
        return invite_code
