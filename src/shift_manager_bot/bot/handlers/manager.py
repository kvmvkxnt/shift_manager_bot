from typing import Any

from aiogram.fsm.context import FSMContext
from aiogram.types import Message


async def cmd_my_team(message: Message, data: dict[str, Any]) -> None:
    pass


async def cmd_create_shift(
    message: Message, state: FSMContext, data: dict[str, Any]
) -> None:
    pass


async def process_shift_date(
    message: Message, state: FSMContext, data: dict[str, Any]
) -> None:
    pass


async def process_shift_time(
    message: Message, state: FSMContext, data: dict[str, Any]
) -> None:
    pass


async def process_shift_max_employees(
    message: Message, state: FSMContext, data: dict[str, Any]
) -> None:
    pass


async def process_shift_note(
    message: Message, state: FSMContext, data: dict[str, Any]
) -> None:
    pass


async def cmd_create_task(
    message: Message, state: FSMContext, data: dict[str, Any]
) -> None:
    pass


async def process_task_title(
    message: Message, state: FSMContext, data: dict[str, Any]
) -> None:
    pass


async def process_task_description(
    message: Message, state: FSMContext, data: dict[str, Any]
) -> None:
    pass


async def process_task_employee(
    message: Message, state: FSMContext, data: dict[str, Any]
) -> None:
    pass


async def process_task_deadline(
    message: Message, state: FSMContext, data: dict[str, Any]
) -> None:
    pass
