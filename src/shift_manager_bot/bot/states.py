from aiogram.fsm.state import State, StatesGroup


class CreateShiftStates(StatesGroup):
    waiting_for_date = State()
    waiting_for_time = State()
    waiting_for_max_employees = State()
    waiting_for_note = State()


class CreateTaskStates(StatesGroup):
    waiting_for_title = State()
    waiting_for_description = State()
    waiting_for_employee = State()
    waiting_for_deadline = State()
