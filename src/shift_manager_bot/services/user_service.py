from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shift_manager_bot.database.models.user import User, UserRole


class UserService:
    async def get_by_telegram_id(
        self, session: AsyncSession, telegram_id: int
    ) -> User | None:
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()

    async def create_user(
        self,
        session: AsyncSession,
        telegram_id: int,
        full_name: str,
        username: str | None = None,
        role: UserRole = UserRole.PENDING,
    ) -> User:
        user = User(
            telegram_id=telegram_id, full_name=full_name, username=username, role=role
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user

    async def get_or_create(
        self,
        session: AsyncSession,
        telegram_id: int,
        full_name: str,
        username: str | None = None,
    ) -> tuple[User, bool]:
        user = await self.get_by_telegram_id(session, telegram_id)
        if user is not None:
            return user, False
        user = await self.create_user(
            session, telegram_id=telegram_id, full_name=full_name, username=username
        )
        return user, True

    async def update_role(
        self, session: AsyncSession, user: User, new_role: UserRole
    ) -> User:
        user.role = new_role
        await session.commit()
        await session.refresh(user)
        return user

    async def deactivate(self, session: AsyncSession, user: User) -> User:
        user.is_active = False
        await session.commit()
        await session.refresh(user)
        return user

    async def get_all_active(
        self, session: AsyncSession, manager_id: int | None = None
    ) -> list[User]:
        query = select(User).where(User.is_active, User.role == UserRole.EMPLOYEE)
        if manager_id is not None:
            query = query.where(User.manager_id == manager_id)
        result = await session.execute(query)
        return list(result.scalars().all())

    async def get_all_managers(self, session: AsyncSession) -> list[User]:
        result = await session.execute(
            select(User).where(User.is_active, User.role == UserRole.MANAGER)
        )
        return list(result.scalars().all())

    async def get_all_teams(self, session: AsyncSession) -> dict[User, list[User]]:
        manager_result = await session.execute(
            select(User).where(User.is_active, User.role == UserRole.MANAGER)
        )
        managers = list(manager_result.scalars().all())

        teams: dict[User, list[User]] = {}
        for manager in managers:
            employees_result = await session.execute(
                select(User).where(
                    User.is_active,
                    User.role == UserRole.EMPLOYEE,
                    User.manager_id == manager.id,
                )
            )
            teams[manager] = list(employees_result.scalars().all())

        return teams
