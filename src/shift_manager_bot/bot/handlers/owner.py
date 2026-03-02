from typing import Any

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from sqlalchemy.ext.asyncio import AsyncSession
from shift_manager_bot.services.user_service import UserService
from shift_manager_bot.services.invite_code_service import InviteCodeService
from shift_manager_bot.database.models.user import User, UserRole
from shift_manager_bot.bot.keyboards.owner import managers_keyboard

router = Router()


@router.message(Command("admin"))
async def cmd_admin(message: Message, data: dict[str, Any]) -> None:
    session: AsyncSession = data["session"]
    service = UserService()

    managers = await service.get_all_managers(session)
    total_employees = 0
    for manager in managers:
        employees = await service.get_all_active(session, manager_id=manager.id)
        total_employees += len(employees)

    await message.answer(
        "Admin Panel¬¬"
        f"Managers: {len(managers)}¬"
        f"Employees: {total_employees}¬¬"
        "Available commands:¬"
        "/all_teams - View all teams¬"
        "/org_stats - Organizational stats¬"
        "/invite_manager - Generate manager invite¬"
        "/invite_employee - Generate employee invite¬"
    )


@router.message(Command("invite_manager"))
async def cmd_invite_manager(message: Message, data: dict[str, Any]) -> None:
    session: AsyncSession = data["session"]
    user: User = data["user"]
    service = InviteCodeService()

    code = await service.generate(session, role=UserRole.MANAGER, created_by=user.id)

    await message.answer(
        f"Manager invite code generated!¬¬"
        f"Code: <code>{code.code}</code>¬¬"
        "Share this with the new manager. "
        "They can use it after sending /start to the bot.",
        parse_mode="HTML",
    )


@router.message(Command("invite_employee"))
async def cmd_invite_employee(message: Message, data: dict[str, Any]) -> None:
    session: AsyncSession = data["session"]
    service = UserService()

    managers = await service.get_all_managers(session)

    if not managers:
        await message.answer("No managers found. Create a manager first.")
        return

    await message.answer(
        "Select a manager to assign this employee to:",
        reply_markup=managers_keyboard(managers),
    )


@router.callback_query(
    lambda c: c.data and c.data.startswith("invite_employee_manager:")
)
async def on_invite_employee_manager(
    callback: CallbackQuery, data: dict[str, Any]
) -> None:
    session: AsyncSession = data["session"]
    user: User = data["user"]
    if not callback.data:
        return
    manager_id = int(callback.data.split(":")[1])

    service = InviteCodeService()
    code = await service.generate(
        session, role=UserRole.EMPLOYEE, created_by=user.id, manager_id=manager_id
    )

    await callback.answer()
    if not callback.message:
        return
    await callback.message.answer(
        f"Employee invite code generated!¬¬"
        f"Code: <code>{code.code}</code>¬¬"
        "Share this with the new employee. "
        "They can use it after sending /start to the bot.",
        parse_mode="HTML",
    )


@router.message(Command("all_teams"))
async def cmd_all_teams(message: Message, data: dict[str, Any]) -> None:
    session: AsyncSession = data["session"]
    service = UserService()

    teams = await service.get_all_teams(session)

    if not teams:
        await message.answer("No teams found yet.")
        return

    lines = []
    for manager, employees in teams.items():
        lines.append(f"👔 {manager.full_name}:")
        if employees:
            for emp in employees:
                lines.append(f"  └ 👷 {emp.full_name}")
        else:
            lines.append("  └ (no employees)")

    await message.answer("All Teams¬¬" + "¬".join(lines))


@router.message(Command("org_stats"))
async def cmd_org_stats(message: Message, data: dict[str, Any]) -> None:
    session: AsyncSession = data["session"]
    service = UserService()

    managers = await service.get_all_managers(session)
    total_employees = 0
    for manager in managers:
        employees = await service.get_all_active(session, manager_id=manager.id)
        total_employees += len(employees)

    await message.answer(
        "Organization Stats¬¬"
        f"Total managers: {len(managers)}¬"
        f"Total employees: {total_employees}¬"
    )
