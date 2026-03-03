from aiogram.filters import Filter
from aiogram.types import CallbackQuery, Message

from shift_manager_bot.database.models.user import User, UserRole


class RoleFilter(Filter):
    def __init__(self, *roles: UserRole) -> None:
        self.roles = roles

    async def __call__(self, _: Message | CallbackQuery, user: User) -> bool:
        return user.role in self.roles


class IsEmployee(RoleFilter):
    def __init__(self) -> None:
        super().__init__(UserRole.EMPLOYEE)


class IsManager(RoleFilter):
    def __init__(self) -> None:
        super().__init__(UserRole.MANAGER)


class IsOwner(RoleFilter):
    def __init__(self) -> None:
        super().__init__(UserRole.OWNER)


class IsManagerOrOwner(RoleFilter):
    def __init__(self) -> None:
        super().__init__(UserRole.MANAGER, UserRole.OWNER)


class IsPendingUser(Filter):
    async def __call__(self, _: Message | CallbackQuery, user: User) -> bool:
        return user.role == UserRole.PENDING
