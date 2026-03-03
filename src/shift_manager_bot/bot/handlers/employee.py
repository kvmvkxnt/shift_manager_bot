from aiogram import Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from shift_manager_bot.bot.callbacks import ShiftCallbackData, TaskCallbackData
from shift_manager_bot.bot.keyboards.employee import shift_keyboard, task_keyboard
from shift_manager_bot.database.models.shift import (
    AssignmentStatus,
    Shift,
    ShiftAssignment,
)
from shift_manager_bot.database.models.task import Task, TaskStatus
from shift_manager_bot.database.models.user import User
from shift_manager_bot.services.shift_service import ShiftService
from shift_manager_bot.services.task_service import TaskService

router = Router()


def format_shift_text(shift: Shift, assignment: ShiftAssignment) -> str:
    return (
        f"Shift #{shift.id}\n"
        f"Time: {shift.starts_at.strftime('%Y-%m-%d %H:%M')} → "
        f"{shift.ends_at.strftime('%H:%M')}\n"
        f"Status: {assignment.status.value.capitalize()}\n"
        f"{f'📝 {shift.note}' if shift.note else ''}"
    ).strip()


def format_task_text(task: Task) -> str:
    deadline_str = (
        f"\nDeadline: {task.deadline.strftime('%Y-%m-%d %H:%M')}"
        if task.deadline
        else ""
    )
    return (
        f"Task #{task.id}: {task.title}\n"
        f"Status: {task.status.value.replace('_', ' ').capitalize()}"
        f"{deadline_str}"
    ).strip()


@router.message(Command("my_shifts"))
async def cmd_my_shifts(message: Message, user: User, session: AsyncSession) -> None:
    service = ShiftService()

    assignments = await service.get_employee_assignments(session, user.id)

    if not assignments:
        await message.answer("You have no upcoming shifts.")
        return

    for assignment in assignments:
        shift = assignment.shift
        await message.answer(
            format_shift_text(shift, assignment),
            reply_markup=shift_keyboard(assignment.id, assignment.status),
        )


@router.callback_query(ShiftCallbackData.filter())
async def on_shift_action(
    callback: CallbackQuery, callback_data: ShiftCallbackData, session: AsyncSession
) -> None:
    service = ShiftService()

    assignment = await service.get_assignment_by_id(
        session, callback_data.assignment_id
    )
    if assignment is None:
        await callback.answer("Assignment not found.")
        return

    if callback_data.action == "confirm":
        await service.update_assignment_status(
            session, assignment, AssignmentStatus.CONFIRMED
        )
        await callback.answer("Shift confirmed!")
    elif callback_data.action == "decline":
        await service.update_assignment_status(
            session, assignment, AssignmentStatus.DECLINED
        )
        await callback.answer("Shift declined.")

    if callback.message:
        if not isinstance(callback.message, Message):
            return

        await callback.message.edit_text(
            format_shift_text(assignment.shift, assignment)
        )


@router.message(Command("my_tasks"))
async def cmd_my_tasks(message: Message, user: User, session: AsyncSession) -> None:
    service = TaskService()

    tasks = await service.get_employee_tasks(session, user.id)

    if not tasks:
        await message.answer("You have no tasks.")
        return

    for task in tasks:
        await message.answer(
            format_task_text(task), reply_markup=task_keyboard(task.id, task.status)
        )


@router.callback_query(TaskCallbackData.filter())
async def on_task_action(
    callback: CallbackQuery, callback_data: TaskCallbackData, session: AsyncSession
) -> None:
    service = TaskService()

    task = await service.get_by_id(session, callback_data.task_id)
    if task is None:
        await callback.answer("Task not found.")
        return

    if callback_data.action == "in_progress":
        await service.update_status(session, task, TaskStatus.IN_PROGRESS)
        await callback.answer("Task marked as in progress!")
    elif callback_data.action == "done":
        await service.update_status(session, task, TaskStatus.DONE)
        await callback.answer("Task marked as done!")

    if callback.message:
        if not isinstance(callback.message, Message):
            return

        await callback.message.edit_text(format_task_text(task))


@router.message(Command("my_stats"))
async def cmd_my_stats(message: Message, user: User, session: AsyncSession) -> None:

    shift_service = ShiftService()
    task_service = TaskService()

    completed_shifts = await shift_service.get_employee_completed_shifts_count(
        session, user.id
    )
    upcoming_shifts = await shift_service.get_employee_upcoming_shifts_count(
        session, user.id
    )
    tasks_done = await task_service.get_employee_tasks_count_by_status(
        session, user.id, TaskStatus.DONE
    )
    tasks_in_progress = await task_service.get_employee_tasks_count_by_status(
        session, user.id, TaskStatus.IN_PROGRESS
    )
    tasks_todo = await task_service.get_employee_tasks_count_by_status(
        session, user.id, TaskStatus.TODO
    )

    await message.answer(
        f"Your stats\n\n"
        f"Shifts:\n"
        f"  Completed: {completed_shifts}\n"
        f"  Upcoming: {upcoming_shifts}\n\n"
        f"Tasks:\n"
        f"  Done: {tasks_done}\n"
        f"  In progress: {tasks_in_progress}\n"
        f"  Todo: {tasks_todo}\n"
    )
