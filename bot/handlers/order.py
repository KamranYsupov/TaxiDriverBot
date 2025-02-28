from aiogram import Router, types, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from asgiref.sync import sync_to_async
from django.db import transaction

from bot.keyboards.inline import get_inline_keyboard
from bot.keyboards.reply import reply_cancel_keyboard, reply_location_keyboard
from bot.states.order import OrderState
from bot.utils.texts import address_string
from bot.valiators.taxi_driver import OrderStateValidator
from web.apps.orders.models import Order
from web.apps.telegram_users.models import TelegramUser
from web.services.api_2gis import api_2gis_service, API2GisError

router = Router()


@router.callback_query(F.data == 'order')
async def choice_order_type_callback_handler(callback: types.CallbackQuery, state: FSMContext):
    buttons = {
        'Такси 🚕': 'order_такси',
        'Доставка 📦': 'order_доставка',
        'Назад 🔙': 'menu_user'
    }

    await callback.message.edit_text(
        'Выберите тип заказа',
        reply_markup=get_inline_keyboard(
            buttons=buttons,
            sizes=(1, 1, 1)
        )
    )

# Обработчик для выбора типа заказа
@router.callback_query(F.data.startswith('order_'))
async def process_order_type_callback_handler(callback: types.CallbackQuery, state: FSMContext):
    order_type = callback.data.split('_')[-1].capitalize()
    await state.update_data(type=order_type)

    await callback.message.delete()
    await callback.message.answer(
        'Нажмите на кнопку <b>"Отправить геолокацию 🏬"</b>'
        'чтобы отправить ваш адресс.',
        reply_markup=reply_location_keyboard
    )
    await state.set_state(OrderState.from_address)


@router.message(OrderState.from_address, F.text)
async def process_from_address(message: types.Message, state: FSMContext):
    # lat = message.location.latitude
    # lon = message.location.longitude
    lat, lon = 55.035049, 82.92005
    from_address = api_2gis_service.get_address(lat, lon)
    from_address_data = {
        'address': from_address,
        'lat': lat,
        'lon': lon
    }
    await state.update_data(from_address=from_address_data)

    await message.answer(
        'Отправьте адрес назначения в формате <b>Город, Улица, Дом</b>\n\n'
        '<b><em>Примеры корректныx адресов:\n\n'
        f'<blockquote>{address_string}</blockquote></em></b>'
    )
    await state.set_state(OrderState.to_address)


@router.message(OrderState.to_address)
async def process_to_address(message: types.Message, state: FSMContext):
    telegram_user = await TelegramUser.objects.aget(telegram_id=message.from_user.id)
    state_data = await state.get_data()

    from_address_data = state_data['from_address']
    from_lat, from_lon = from_address_data['lat'], from_address_data['lon']

    to_address = message.text

    try:
        to_lat, to_lon = api_2gis_service.get_cords(to_address)

        order_data = {
            'type': state_data['type'],
            'telegram_user_id': telegram_user.id,

            'from_address': from_address_data['address'],
            'from_latitude': from_lat,
            'from_longitude': from_lon,

            'to_address': to_address,
            'to_latitude': to_lat,
            'to_longitude': to_lon,

        }

        await Order.objects.acreate(**order_data)
        
    except API2GisError as e:
        await message.answer(str(e))
        return

    await message.answer('Поиск водителей...')
    await state.clear()


@router.message(Command('cancel'), ~StateFilter(default_state))
async def cancel_order(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer('Заказ отменен!')