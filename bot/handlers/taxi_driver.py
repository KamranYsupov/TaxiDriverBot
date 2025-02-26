from typing import Optional

from aiogram import Router, types, F
from aiogram.filters import CommandStart, Command, StateFilter
from aiogram.fsm.context import FSMContext
from django.core.files.images import ImageFile

from bot.keyboards.inline import get_inline_keyboard, inline_driver_keyboard
from bot.keyboards.reply import reply_contact_keyboard, reply_keyboard_remove, reply_cancel_keyboard
from bot.states.taxi_driver import CarState
from bot.valiators.taxi_driver import CarStateValidator

from web.apps.telegram_users.models import TelegramUser, TaxiDriver, Car
from web.services.telegram_service import async_telegram_service

router = Router()


async def is_car_approved_handler(
        callback: types.CallbackQuery,
        car: Optional[Car] = None
):
    if not car:
        taxi_driver: TaxiDriver = await TaxiDriver.objects.aget(
            telegram_id=callback.from_user.id,
        )
        car: Car = await Car.objects.aget(driver=taxi_driver)

    if car.status == Car.APPROVED:
        return True

    if car.status == Car.WAITING:
        message_text = 'Ожидайте. Авто на проверке.'
    else:
        message_text = 'Сначала зарегестрируйте авто'

    await callback.message.edit_text(
        message_text,
        reply_markup=get_inline_keyboard(
            buttons={'Назад 🔙': 'menu_driver'}
        )
    )



@router.callback_query(F.data == 'child_chair')
async def child_chair_callback_handler(callback: types.CallbackQuery):
    taxi_driver: TaxiDriver = await TaxiDriver.objects.aget(
        telegram_id=callback.from_user.id,
    )
    car: Car = await Car.objects.aget(driver=taxi_driver)

    if not await is_car_approved_handler(callback, car):
        return

    button_text = 'Включить ✅' if not taxi_driver.child_chair else 'Выключить ❌'
    message_text = (
        'Детское кресло: '
        f'<b>{"включено ✅" if taxi_driver.child_chair else "выключено ❌"}</b>'
    )
    buttons = {
        button_text: 'driver_change-child_chair',
        'Назад 🔙': 'menu_driver',
    }

    await callback.message.edit_text(
        message_text,
        reply_markup=get_inline_keyboard(
            buttons=buttons,
            sizes=(1, 1, 1)
        ),
    )


@router.callback_query(F.data == 'in_work')
async def in_work_callback_handler(callback: types.CallbackQuery):
    taxi_driver: TaxiDriver = await TaxiDriver.objects.aget(
        telegram_id=callback.from_user.id,
    )
    car: Car = await Car.objects.aget(driver=taxi_driver)

    if not await is_car_approved_handler(callback, car):
        return

    button_text = 'Включить ✅' if not taxi_driver.in_work else 'Выключить ❌'
    message_text = (
        'Смена: '
        f'<b>{"включена ✅" if taxi_driver.in_work else "выключена ❌"}</b>'
    )
    buttons = {
        button_text: 'driver_change-in_work',
        'Назад 🔙': 'menu_driver',
    }

    await callback.message.edit_text(
        message_text,
        reply_markup=get_inline_keyboard(
            buttons=buttons,
            sizes=(1, 1, 1)
        ),
    )


@router.callback_query(F.data.startswith('driver_change-'))
async def driver_change_field_callback_handler(callback: types.CallbackQuery):
    change_field_name = callback.data.split('-')[-1]
    if change_field_name not in ('child_chair', 'in_work'):
        return

    taxi_driver: TaxiDriver = await TaxiDriver.objects.aget(
        telegram_id=callback.from_user.id,
    )
    change_field_value = getattr(taxi_driver, change_field_name)  # Достаём значение нужного поля
    setattr(taxi_driver, change_field_name, not change_field_value)  # Изменяем значение нужного поля

    await taxi_driver.asave()

    if change_field_name == 'child_chair':
        await child_chair_callback_handler(callback)
    elif change_field_name == 'in_work':
        await in_work_callback_handler(callback)