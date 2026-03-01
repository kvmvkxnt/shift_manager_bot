from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from shift_manager_bot.database.models.user import User


def employees_keyboard(employees: list[User]) -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(
                text=f"{e.full_name} (@{e.username})" if e.username else e.full_name,
                callback_data=f"assign_employee:{e.id}",
            )
        ]
        for e in employees
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
