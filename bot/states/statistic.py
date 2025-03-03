from aiogram.fsm.state import StatesGroup, State


class DateState(StatesGroup):
    year = State()
    month = State()
    day = State()