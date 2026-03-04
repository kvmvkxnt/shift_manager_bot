from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


class DbSessionMiddleware(BaseMiddleware):
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        self.session_factory = session_factory

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        session = self.session_factory()
        if hasattr(session, "__aenter__"):
            async with session as s:
                data["session"] = s
                return await handler(event, data)
        else:
            # Check if it's a coroutine (test mock)
            import asyncio
            if asyncio.iscoroutine(session):
                session = await session
            
            data["session"] = session
            try:
                return await handler(event, data)
            finally:
                if hasattr(session, "close"):
                    await session.close()
