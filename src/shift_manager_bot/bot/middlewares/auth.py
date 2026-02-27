from typing import Any
from unittest.mock import AsyncMock

from aiogram.types import Message


class AuthMiddleware:
    async def __call__(
        self, handler: AsyncMock, message: Message, data: dict[str, Any]
    ) -> None:
        pass
