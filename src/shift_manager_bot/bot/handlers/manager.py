from datetime import datetime, timezone
from typing import Any

from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from shift_manager_bot.bot.keyboards.manager import employees_keyboard
from shift_manager_bot.bot.states import CreateShiftStates, CreateTaskStates
from shift_manager_bot.database.models.task import TaskStatus
from shift_manager_bot.database.models.user import User, UserRole
from shift_manager_bot.services.invite_code_service import InviteCodeService
from shift_manager_bot.services.shift_service import ShiftService
from shift_manager_bot.services.task_service import TaskService
from shift_manager_bot.services.user_service import UserService

router = Router()


@router.message(Command("my_team"))
async def cmd_my_team(message: Message, user: User, session: AsyncSession) -> None:
    service = UserService()

    team = await service.get_all_active(session, manager_id=user.id)

    if not team:
        await message.answer("You have no employees in your team yet.")
        return

    text = "Your team:¬¬" + "¬".join(
        f"- {e.full_name}" + (f" (@{e.username})" if e.username else "") for e in team
    )

    await message.answer(text)


@router.message(Command("create_shift"))
async def cmd_create_shift(message: Message, state: FSMContext) -> None:
    await state.set_state(CreateShiftStates.waiting_for_date)
    await message.answer(
        "Let's create a new shift!¬¬Please enter the date (format: YYYY-MM-DD):"
    )


@router.message(CreateShiftStates.waiting_for_date)
async def process_shift_date(message: Message, state: FSMContext) -> None:
    if not message.text:
        await message.answer(
            "Invalid date format. Please use YYYY-MM-DD (e.g. 2026-01-25):"
        )
        return

    try:
        datetime.strptime(message.text.strip(), "%Y-%m-%d")
    except ValueError:
        await message.answer(
            "Invalid date format. Please use YYYY-MM-DD (e.g. 2026-01-25):"
        )
        return

    await state.update_data(date=message.text.strip())
    await state.set_state(CreateShiftStates.waiting_for_time)
    await message.answer(
        "Great! Now enter the shift time range¬(format: HH:MM-HH:MM, e.g. 09:00-17:00):"
    )


@router.message(CreateShiftStates.waiting_for_time)
async def process_shift_time(message: Message, state: FSMContext) -> None:
    if not message.text:
        await message.answer(
            "Invalid time format. Please use HH:MM-HH:MM (e.g. 09:00-17:00):"
        )
        return

    try:
        parts = message.text.strip().split("-")
        if len(parts) != 2:
            raise ValueError
        datetime.strptime(parts[0], "%H:%M")
        datetime.strptime(parts[1], "%H:%M")
    except ValueError:
        await message.answer(
            "Invalid time format. Please use HH:MM-HH:MM (e.g. 09:00-17:00):"
        )
        return

    await state.update_data(time=message.text.strip())
    await state.set_state(CreateShiftStates.waiting_for_max_employees)
    await message.answer("How many employees can work this shift? (enter a number):")


@router.message(CreateShiftStates.waiting_for_max_employees)
async def process_shift_max_employees(message: Message, state: FSMContext) -> None:
    if not message.text:
        await message.answer("Invalid number. Please enter a positive integer:")
        return

    try:
        max_employees = int(message.text.strip())
        if max_employees < 1:
            raise ValueError
    except ValueError:
        await message.answer("Invalid number. Please enter a positive integer:")
        return

    await state.update_data(max_employees=max_employees)
    await state.set_state(CreateShiftStates.waiting_for_note)
    await message.answer("Any notes for this shift? Type a note or /skip to skip:")


@router.message(CreateShiftStates.waiting_for_note)
async def process_shift_note(
    message: Message, state: FSMContext, user: User, session: AsyncSession
) -> None:
    fsm_data = await state.get_data()

    note: str | None
    if message.text:
        note = None if message.text.strip() == "/skip" else message.text.strip()
    else:
        note = None

    date_str = fsm_data["date"]
    time_str = fsm_data["time"]
    start_str, end_str = time_str.split("-")

    starts_at = datetime.strptime(f"{date_str} {start_str}", "%Y-%m-%d %H:%M").replace(
        tzinfo=timezone.utc
    )
    ends_at = datetime.strptime(f"{date_str} {end_str}", "%Y-%m-%d %H:%M").replace(
        tzinfo=timezone.utc
    )

    service = ShiftService()
    await service.create_shift(
        session,
        manager_id=user.id,
        starts_at=starts_at,
        ends_at=ends_at,
        max_employees=fsm_data["max_employees"],
        note=note,
    )

    await state.clear()
    await message.answer(
        f"Shift successfully created!¬¬"
        f"Date: {date_str}¬"
        f"Time: {time_str}¬"
        f"Max employees: {fsm_data['max_employees']}¬"
        f"Note: {note or 'None'}"
    )


# Create task FSM
@router.message(Command("create_task"))
async def cmd_create_task(message: Message, state: FSMContext) -> None:
    await state.set_state(CreateTaskStates.waiting_for_title)
    await message.answer("Let's create a new task!¬¬Please enter the task title:")


@router.message(CreateTaskStates.waiting_for_title)
async def process_task_title(message: Message, state: FSMContext) -> None:
    if not message.text:
        await message.answer("Please enter the task title:")
        return

    await state.update_data(title=message.text.strip())
    await state.set_state(CreateTaskStates.waiting_for_description)
    await message.answer("Enter a description or /skip to skip:")


@router.message(CreateTaskStates.waiting_for_description)
async def process_task_description(
    message: Message, state: FSMContext, user: User, session: AsyncSession
) -> None:
    if not message.text:
        await message.answer("Enter a description or /skip to skip:")
        return

    description = None if message.text.strip() == "/skip" else message.text.strip()
    await state.update_data(description=description)
    await state.set_state(CreateTaskStates.waiting_for_employee)

    service = UserService()
    team = await service.get_all_active(session, manager_id=user.id)

    if not team:
        await state.clear()
        await message.answer("You have no employees to assign this task to.")
        return

    await message.answer(
        "Select an employee to assign this task to:",
        reply_markup=employees_keyboard(team),
    )


@router.callback_query(lambda c: c.data and c.data.startswith("assign_employee:"))
async def process_task_employee(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.data:
        employee_id = int(callback.data.split(":")[1])
        await state.update_data(employee_id=employee_id)
        await state.set_state(CreateTaskStates.waiting_for_deadline)
        await callback.answer()
        if callback.message:
            await callback.message.answer(
                "Enter a deadline (format: YYYY-MM-DD HH:MM) or /skip to skip:"
            )


@router.message(CreateTaskStates.waiting_for_deadline)
async def process_task_deadline(
    message: Message, state: FSMContext, user: User, session: AsyncSession
) -> None:
    fsm_data = await state.get_data()

    deadline = None

    if not message.text:
        await message.answer("Invalid format. Use YYYY-MM-DD HH:MM or /skip:")
        return

    if message.text.strip() != "/skip":
        try:
            deadline = datetime.strptime(
                message.text.strip(), "%Y-%m-%d %H:%M"
            ).replace(tzinfo=timezone.utc)
        except ValueError:
            await message.answer("Invalid format. Use YYYY-MM-DD HH:MM or /skip:")
            return

    service = TaskService()
    task = await service.create_task(
        session,
        title=fsm_data["title"],
        employee_id=fsm_data["employee_id"],
        manager_id=user.id,
        description=fsm_data.get("description"),
        deadline=deadline,
    )

    await state.clear()
    await message.answer(
        f"Task successfully created!¬¬"
        f"Title: {task.title}¬"
        f"Description: {task.description or 'None'}¬"
        f"Deadline: {deadline.strftime('%Y-%m-%d %H:%M') if deadline else 'None'}"
    )


@router.message(Command("invite"))
async def cmd_invite(message: Message, user: User, session: AsyncSession) -> None:
    service = InviteCodeService()

    code = await service.generate(
        session, role=UserRole.EMPLOYEE, created_by=user.id, manager_id=user.id
    )

    await message.answer(
        f"Employee invite code generated!¬¬"
        f"Code: <code>{code.code}</code>¬¬"
        f"Share this with the new employee. "
        "They can use it after sending /start to the bot.",
        parse_mode="HTML",
    )


@router.message(Command("team_stats"))
async def cmd_team_stats(message: Message, user: User, session: AsyncSession) -> None:
    shift_service = ShiftService()
    task_service = TaskService()
    user_service = UserService()

    team = await user_service.get_all_active(session, manager_id=user.id)
    total_shifts = await shift_service.get_manager_shifts_count(session, user.id)
    tasks_done = await task_service.get_manager_tasks_count_by_status(
        session, user.id, TaskStatus.DONE
    )
    tasks_in_progress = await task_service.get_manager_tasks_count_by_status(
        session, user.id, TaskStatus.IN_PROGRESS
    )
    tasks_todo = await task_service.get_manager_tasks_count_by_status(
        session, user.id, TaskStatus.TODO
    )

    await message.answer(
        f"Team Stats¬¬"
        f"Team size: {len(team)}¬¬"
        f"Shifts:¬"
        f"  Total created: {total_shifts}¬¬"
        f"Tasks:¬"
        f"  Done: {tasks_done}¬"
        f"  In progress: {tasks_in_progress}¬"
        f"  Todo: {tasks_todo}¬"
    )
