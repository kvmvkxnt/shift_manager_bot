from typing import Any

from aiogram.types import CallbackQuery, Message

from shift_manager_bot.bot.callbacks import ShiftCallbackData, TaskCallbackData


async def cmd_my_shifts(message: Message, data: dict[str, Any]) -> Any:
    pass


async def on_shift_action(
    callback: CallbackQuery, callback_data: ShiftCallbackData, data: dict[str, Any]
) -> Any:
    pass


async def cmd_my_tasks(message: Message, data: dict[str, Any]) -> Any:
    pass


async def on_task_action(
    callback: CallbackQuery, callback_data: TaskCallbackData, data: dict[str, Any]
) -> Any:
    pass
