from aiogram.fsm.state import StatesGroup, State


class WriteOffPointsState(StatesGroup):
    points_count = State()
    obj = State() # Order или Product


