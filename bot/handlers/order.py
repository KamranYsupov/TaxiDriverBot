import uuid
from typing import Union

from aiogram import Router, types, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from asgiref.sync import sync_to_async

from bot.keyboards.inline import get_inline_keyboard
from bot.keyboards.reply import reply_cancel_keyboard, reply_location_keyboard, reply_keyboard_remove
from bot.orm.payment import create_order_payment
from bot.states.order import OrderState
from bot.states.points import WriteOffPointsState
from bot.utils.texts import address_string
from bot.valiators.taxi_driver import OrderStateValidator
from web.apps.orders.models import Order, Payment, OrderType, OrderPriceSettings
from web.apps.products.models import Product
from web.apps.telegram_users.models import TelegramUser, TaxiDriver
from web.services.api_2gis import api_2gis_service, API2GisError
from web.services.yookassa import create_yookassa_payment

router = Router()


@router.callback_query(F.data == 'order')
async def choice_order_type_callback_handler(
        callback: types.CallbackQuery
):
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


@router.callback_query(F.data.startswith('order_'))
async def process_order_type_callback_handler(
        callback: types.CallbackQuery,
        state: FSMContext
):
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
async def process_from_address(
        message: types.Message,
        state: FSMContext
):
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
        f'<blockquote>{address_string}</blockquote></em></b>',
        reply_markup=reply_cancel_keyboard,
    )
    await state.set_state(OrderState.to_address)


@router.message(OrderState.to_address)
async def process_to_address(message: types.Message, state: FSMContext):
    await message.answer(
        '<em>Анализирую маршрут . . .</em>',
        reply_markup=reply_keyboard_remove,
    )

    telegram_user = await TelegramUser.objects.aget(
        telegram_id=message.from_user.id
    )
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

    await message.answer('<em>Поиск водителей . . .</em>')
    await state.clear()


@router.callback_query(F.data.startswith('accept_order_'))
async def accept_order_callback_handler(callback: types.CallbackQuery):
    order_id, driver_id = callback.data.split('_')[-2:]
    order: Order = await Order.objects.aget(id=order_id)
    taxi_driver: TaxiDriver = await TaxiDriver.objects.aget(id=driver_id)

    await callback.message.edit_reply_markup(reply_markup=None)

    if order.driver_id:
        await callback.message.edit_text(
            '<b><em>Вы уже выбрали водителя</em></b>'
        )
        return

    order.driver_id = taxi_driver.id
    await order.asave()

    telegram_user = await TelegramUser.objects.aget(
        telegram_id=callback.from_user.id
    )

    if not telegram_user.points:
        yookassa_payment_response = await create_order_payment(order_id=order_id)

        reply_markup = InlineKeyboardMarkup(
            inline_keyboard=[[
                InlineKeyboardButton(
                    text="Оплатить 💳",
                    url=yookassa_payment_response.confirmation.confirmation_url
                )
            ]]
        )
        points = yookassa_payment_response.metadata.get('points')
        await callback.message.edit_text(
            'Оплата поездки. После оплаты водитель направиться к вам.\n'
            f'Начислим {points} баллов.\n\n'
            '<b>ВАЖНО:</b> после оплаты обязательно нажмите '
            'на кнопку <b><em>"Вернуться на сайт"</em></b>, '
            'чтобы завершить заказ.',
            reply_markup=reply_markup,
        )
        return

    await callback.message.answer(
        f'Хотите списать баллы?\n\n'
        f'<em>Баллы оплачивают до 50% от поездки</em>.',
        reply_markup=get_inline_keyboard(
            buttons={
                f'Списать баллы ({telegram_user.points}) 💸': \
                    f'write_off_points_order_{order.id}',
                'Оплатить полностью 💳': f'send_payment_order_{order.id}',
            }
        )
    )


@router.callback_query(F.data.startswith('send_payment_order_'))
async def send_payment_order_callback_handler(callback: types.CallbackQuery):
    order_id = callback.data.split('_')[-1]
    yookassa_payment_response = await create_order_payment(order_id=order_id)

    reply_markup = InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(
                text="Оплатить 💳",
                url=yookassa_payment_response.confirmation.confirmation_url
            )
        ]]
    )
    points = yookassa_payment_response.metadata.get('points')
    await callback.message.edit_text(
        'Оплата поездки. После оплаты водитель направиться к вам.\n'
        f'Начислим {points} баллов.\n\n'
        '<b>ВАЖНО:</b> после оплаты обязательно нажмите '
        'на кнопку <b><em>"Вернуться на сайт"</em></b>, '
        'чтобы завершить заказ.',
        reply_markup=reply_markup,
    )


@router.callback_query(F.data.startswith('write_off_points_'))
async def write_off_points_callback_handler(
        callback: types.CallbackQuery,
        state: FSMContext
):
    obj_type, obj_id = callback.data.split('_')[-2:]
    model = Order if obj_type == 'order' else Product

    obj: Union[Order, Product] = await model.objects.aget(id=obj_id)

    await state.update_data(obj=obj)
    await state.set_state(WriteOffPointsState.points_count)

    await callback.message.edit_text(
        'Отправьте количество баллов для списания',
        reply_markup=None
    )


@router.message(F.text, WriteOffPointsState.points_count)
async def process_points_count_handler(
        message: types.Message,
        state: FSMContext
):
    try:
        points_count = int(message.text)
    except ValueError:
        await message.answer('Пожалуйста, отправьте корректное число баллов.')
        return

    state_data = await state.get_data()
    obj: Union[Order, Product] = state_data.get('obj')

    payment_kwargs = {}
    if isinstance(obj, Order):
        obj_string = 'заказ'
        payment_kwargs['order_id'] = obj.id
    else:
        obj_string = 'товар'
        payment_kwargs['product_id'] = obj.id

    if points_count > obj.price / 2:
        await message.answer(
            f'Нельзя списать более 50% от стоимости {obj_string}а'
        )
        return

    payment_kwargs['price'] = obj.price - points_count
    telegram_user: TelegramUser = await TelegramUser.objects.aget(
        telegram_id=message.from_user.id
    )

    try:
        telegram_user.points -= points_count
    except Exception:
        await message.answer('Произошла ошибка', )
        return
    finally:
        await telegram_user.asave()

    await message.answer('Баллы успешно списаны ✅')
    yookassa_payment_response = await create_order_payment(**payment_kwargs)
    await message.answer(
        'Оплата поездки. После оплаты водитель направиться к вам.\n\n'
        '<b>ВАЖНО:</b> после оплаты обязательно нажмите '
        'на кнопку <b><em>"Вернуться на сайт"</em></b>, '
        'чтобы завершить заказ.',
        reply_markup=InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(
                text="Оплатить 💳",
                url=yookassa_payment_response.confirmation.confirmation_url
            )
        ]]
    ),
    )
