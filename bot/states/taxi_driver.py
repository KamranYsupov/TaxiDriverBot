from aiogram.fsm.state import StatesGroup, State


class TaxiDriverState(StatesGroup):
    full_name = State()
    phone_number = State()
    passport_data = State()
    passport_photo = State()


class CarState(StatesGroup):
    name = State()
    gos_number = State()
    vin = State()
    front_photo = State()
    profile_photo = State()
