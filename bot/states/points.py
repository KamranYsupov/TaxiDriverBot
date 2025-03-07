from aiogram.fsm.state import StatesGroup, State


class WriteOffPointsState(StatesGroup):
    points_count = State()
    obj_id = State() # Order.id или Product.id
    obj_model = State() # Order или Product


