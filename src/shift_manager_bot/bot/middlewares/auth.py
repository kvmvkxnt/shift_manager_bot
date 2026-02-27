from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject

from shift_manager_bot.services.user_service import UserService


class AuthMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if not isinstance(event, Message):
            return await handler(event, data)

        if event.from_user is None:
            return await handler(event, data)

        session = data.get("session")
        if session is None:
            return await handler(event, data)

        tg_user = event.from_user
        service = UserService()
        user, _ = await service.get_or_create(
            session,
            telegram_id=tg_user.id,
            full_name=tg_user.first_name,
            username=tg_user.username,
        )
        data["user"] = user

        return await handler(event, data)
