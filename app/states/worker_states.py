from aiogram.fsm.state import State, StatesGroup


class WorkerStates(StatesGroup):
    waiting_repair_description = State()
    confirming_estimate = State()
