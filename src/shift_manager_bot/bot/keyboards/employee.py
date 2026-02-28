from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from shift_manager_bot.bot.callbacks import ShiftCallbackData, TaskCallbackData
from shift_manager_bot.database.models.shift import AssignmentStatus
from shift_manager_bot.database.models.task import TaskStatus


def shift_keyboard(
    assignment_id: int, status: AssignmentStatus
) -> InlineKeyboardMarkup:
    buttons: list[InlineKeyboardButton] = []
    if status != AssignmentStatus.CONFIRMED:
        buttons.append(
            InlineKeyboardButton(
                text="Confirm",
                callback_data=ShiftCallbackData(
                    action="confirm", assignment_id=assignment_id
                ).pack(),
            )
        )
    if status != AssignmentStatus.DECLINED:
        buttons.append(
            InlineKeyboardButton(
                text="Decline",
                callback_data=ShiftCallbackData(
                    action="decline", assignment_id=assignment_id
                ).pack(),
            )
        )
    return InlineKeyboardMarkup(inline_keyboard=[buttons])


def task_keyboard(task_id: int, status: TaskStatus) -> InlineKeyboardMarkup:
    buttons: list[InlineKeyboardButton] = []
    if status == TaskStatus.TODO:
        buttons.append(
            InlineKeyboardButton(
                text="Start",
                callback_data=TaskCallbackData(
                    action="in_progress", task_id=task_id
                ).pack(),
            )
        )
    if status in (TaskStatus.TODO, TaskStatus.IN_PROGRESS):
        buttons.append(
            InlineKeyboardButton(
                text="Done",
                callback_data=TaskCallbackData(action="done", task_id=task_id).pack(),
            )
        )
    return InlineKeyboardMarkup(inline_keyboard=[buttons])
