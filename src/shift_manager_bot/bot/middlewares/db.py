from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from sqlalchemy.ext.asyncio import AsyncSession


class DbSessionMiddleware(BaseMiddleware):
    def __init__(
        self,
        session_factory: Callable[[], Awaitable[AsyncSession]],
    ) -> None:
        self.session_factory = session_factory

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        session = await self.session_factory()
        data["session"] = session
        return await handler(event, data)
