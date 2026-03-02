from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from shift_manager_bot.database.models.user import User


def managers_keyboard(managers: list[User]) -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(
                text=f"{m.full_name} (@{m.username})" if m.username else m.full_name,
                callback_data=f"invite_employee_manager:{m.id}",
            )
        ]
        for m in managers
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
