import asyncio
import logging

import uvicorn
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from shift_manager_bot.api.router import app
from shift_manager_bot.bot.handlers import common, employee, manager, owner
from shift_manager_bot.bot.middlewares.auth import AuthMiddleware
from shift_manager_bot.bot.middlewares.db import DbSessionMiddleware
from shift_manager_bot.config import settings
from shift_manager_bot.database.session import async_session_factory, engine
from shift_manager_bot.scheduler.setup import create_scheduler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def start_bot(bot: Bot, dp: Dispatcher) -> None:
    logger.info("Starting bot polling...")
    await dp.start_polling(bot)


async def start_api() -> None:
    logger.info("Starting FastAPI...")
    config = uvicorn.Config(app=app, host="0.0.0.0", port=8000, loop="asyncio")
    server = uvicorn.Server(config)
    await server.serve()


async def main() -> None:
    bot = Bot(token=settings.bot_token)
    dp = Dispatcher(storage=MemoryStorage())

    dp.update.middleware(DbSessionMiddleware(session_factory=async_session_factory))
    dp.update.middleware(AuthMiddleware())

    dp.include_router(common.router)
    dp.include_router(employee.router)
    dp.include_router(manager.router)
    dp.include_router(owner.router)

    scheduler = create_scheduler(bot, async_session_factory)
    scheduler.start()
    logger.info("Scheduler started.")

    try:
        await asyncio.gather(start_bot(bot, dp), start_api())
    finally:
        scheduler.shutdown()
        await bot.session.close()
        await engine.dispose()
        logger.info("Shutdown complete.")


if __name__ == "__main__":
    asyncio.run(main())
