from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from aiogram.types import User as TelegramUser

from shift_manager_bot.services.user_service import UserService


class AuthMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        tg_user: TelegramUser | None = data.get("event_from_user")
        if tg_user is None:
            return await handler(event, data)

        session = data.get("session")
        if session is None:
            return await handler(event, data)

        service = UserService()
        user, _ = await service.get_or_create(
            session,
            telegram_id=tg_user.id,
            full_name=tg_user.first_name,
            username=tg_user.username,
        )
        data["user"] = user

        return await handler(event, data)
