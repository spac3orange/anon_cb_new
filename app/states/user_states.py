from aiogram.fsm.state import StatesGroup, State


class StartDialog(StatesGroup):
    dialog_data = State()