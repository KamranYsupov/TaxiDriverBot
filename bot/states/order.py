from aiogram.fsm.state import StatesGroup, State


class OrderState(StatesGroup):
    type = State()
    from_address = State()
    to_address = State()
