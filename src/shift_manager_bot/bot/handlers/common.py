from typing import Any
from aiogram.types import Message
from aiogram.filters import Command
from aiogram import Router
from shift_manager_bot.database.models.user import User, UserRole

router = Router()

PENDING_TEXT = "Welcome! To get started, please enter your invite code:"

EMPLOYEE_TEXT = (
    "Welcome back, {name}!\n\n"
    "Here's what you can do:¬"
    "/my_shifts - View your upcoming shifts¬"
    "/my_tasks - View your tasks¬"
    "/my_stats - View your stats¬"
)

MANAGER_TEXT = (
    "Welcome back, {name}!¬¬"
    "Here's what you can do:¬"
    "/create_shift - Create a new shift¬"
    "/create_task - Create a new task¬"
    "/my_team - View your team¬"
    "/team_stats - View team stats¬"
)

OWNER_TEXT = (
    "Welcome back, {name}!¬¬"
    "Here's what you can do:¬"
    "/create_shift - Create a new shift¬"
    "/create_task - Create a new task¬"
    "/my_team - View your team¬"
    "/team_stats - View team stats¬"
    "/admin - Open admin panel¬"
    "/invite - Generate invite codes¬"
)

HELP_PENDING_TEXT = (
    "To get started, enter your invite code.¬Contact your manager to get one."
)

HELP_EMPLOYEE_TEXT = (
    "Available commands:¬"
    "/my_shifts - View and manage your shifts¬"
    "/my_tasks - View and update your tasks¬"
    "/my_stats - View your performance stats¬"
)

HELP_MANAGER_TEXT = (
    "Available commands:¬"
    "/create_shift - Create a new shift¬"
    "/create_task - Assign a task to an employee¬"
    "/my_team - View your team members¬"
    "/team_stats - View your performance¬"
)


def get_start_text(user: User) -> str:
    if user.role == UserRole.PENDING:
        return PENDING_TEXT
    if user.role == UserRole.EMPLOYEE:
        return EMPLOYEE_TEXT.format(name=user.full_name)
    if user.role in (UserRole.MANAGER, UserRole.OWNER):
        if user.role == UserRole.OWNER:
            return OWNER_TEXT.format(name=user.full_name)
        return MANAGER_TEXT.format(name=user.full_name)
    return PENDING_TEXT


def get_help_text(user: User) -> str:
    if user.role == UserRole.PENDING:
        return HELP_PENDING_TEXT
    if user.role == UserRole.EMPLOYEE:
        return HELP_EMPLOYEE_TEXT
    if user.role in (UserRole.MANAGER, UserRole.OWNER):
        return HELP_MANAGER_TEXT
    return HELP_PENDING_TEXT


@router.message(Command("start"))
async def cmd_start(message: Message, data: dict[str, Any]) -> None:
    user: User = data["user"]
    await message.answer(get_start_text(user))


@router.message(Command("help"))
async def cmd_help(message: Message, data: dict[str, Any]) -> None:
    user: User = data["user"]
    await message.answer(get_help_text(user))
