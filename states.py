from aiogram.fsm.state import State, StatesGroup


class UploadFlow(StatesGroup):
    collecting = State()
    waiting_name = State()
    waiting_description = State()
