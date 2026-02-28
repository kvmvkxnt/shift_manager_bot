from aiogram.filters.callback_data import CallbackData


class ShiftCallbackData(CallbackData, prefix="shift"):
    action: str  # confirm / decline
    assignment_id: int


class TaskCallbackData(CallbackData, prefix="task"):
    action: str  # in_progress / done
    task_id: int
