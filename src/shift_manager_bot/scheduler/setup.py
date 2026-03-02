from apscheduler.schedulers.asyncio import AsyncIOScheduler

from aiogram import Bot

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from shift_manager_bot.scheduler.jobs import send_shift_reminders


def create_scheduler(
    bot: Bot, session_factory: async_sessionmaker[AsyncSession]
) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()

    async def reminder_job() -> None:
        async with session_factory() as session:
            await send_shift_reminders(bot, session)

    scheduler.add_job(
        reminder_job,
        trigger="interval",
        minutes=15,
        id="shift_reminders",
        replace_existing=True,
    )

    return scheduler
