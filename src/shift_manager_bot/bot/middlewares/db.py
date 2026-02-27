from typing import Any, Awaitable, Callable
from unittest.mock import AsyncMock

from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession


class DbSessionMiddleware:
    def __init__(
        self,
        session_factory: Callable[[], AsyncSession]
        | Callable[[], Awaitable[AsyncSession]],
    ) -> None:
        pass

    async def __call__(
        self, handler: AsyncMock, event: Message, data: dict[str, Any]
    ) -> None:
        pass
