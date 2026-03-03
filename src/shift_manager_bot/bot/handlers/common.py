from typing import Any

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from shift_manager_bot.database.models.user import User, UserRole
from shift_manager_bot.services.invite_code_service import InviteCodeService
from shift_manager_bot.services.user_service import UserService

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
async def cmd_start(message: Message, user: User) -> None:
    await message.answer(get_start_text(user))


@router.message(Command("help"))
async def cmd_help(message: Message, user: User) -> None:
    await message.answer(get_help_text(user))


@router.message(lambda message: True)
async def handle_invite_code(
    message: Message, user: User, session: AsyncSession
) -> None:
    if user.role != UserRole.PENDING:
        return

    if not message.text:
        await message.answer("Invalid code. Please try again.")
        return

    code_str = message.text.strip()
    invite_service = InviteCodeService()
    is_valid, error = await invite_service.validate(session, code_str)

    if not is_valid:
        await message.answer(
            f"Invalid or expired code: {error}¬Please check your code and try again."
        )
        return

    invite_code = await invite_service.get_by_code(session, code_str)

    if not invite_code:
        await message.answer("Could not find code. Please try again.")
        return

    await invite_service.redeem(session, invite_code, user.id)

    user_service = UserService()
    await user_service.update_role(session, user, invite_code.role)

    if invite_code.manager_id:
        user.manager_id = invite_code.manager_id
        await session.commit()

    await message.answer(
        f"Welcome! You've been registered as {invite_code.role.value.capitalize()}.¬¬"
        + get_start_text(user)
    )
