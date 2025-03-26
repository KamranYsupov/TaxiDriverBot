import uuid
from typing import Union

from aiogram import Router, types, F, Bot
from aiogram.filters import or_f
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from asgiref.sync import sync_to_async
from django.conf import settings

from bot.keyboards.inline import get_inline_keyboard, get_link_button_inline_keyboard
from bot.keyboards.reply import reply_cancel_keyboard, reply_location_keyboard, reply_keyboard_remove
from bot.orm.payment import create_payment
from bot.states.order import OrderState
from bot.states.points import WriteOffPointsState
from bot.utils.location import get_message_address
from bot.utils.texts import address_string
from bot.valiators.taxi_driver import OrderStateValidator
from web.apps.orders.models import Order, Payment, OrderPriceSettings
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
        'Такси 🚕': 'order_taxi',
        'Доставка 📦': 'order_delivery',
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
         'Отправьте вашу геолокацию, или введите адрес вручную '
         'в формате <em><b>Город, улица дом</b></em>.',
        reply_markup=reply_cancel_keyboard,
    )
    await state.set_state(OrderState.from_address)


async def validate_address_city(message: types.Message, from_address: str):
    from_address_city = from_address.split(',')[0]
    return from_address_city in settings.ORDER_CITIES


async def send_order_message(
        message: types.Message,
        from_address: str,
        to_address: str,
):
    await message.answer(
        '<b>Данные поездки:</b>\n\n'
        f'<b>Адрес отправки:</b> <em>{from_address}</em>\n'
        f'<b>Адрес назначения:</b> <em>{to_address}</em>\n',
        reply_markup=get_inline_keyboard(
            buttons={
                'Указать другой адрес отправки ✍️': 'edit_from_address',
                'Указать другой адрес назначения ✍️': 'edit_to_address',
                'Все верно ✅': 'create_order',
            },
            sizes=(1, 1, 1)
        )
    )


@router.message(
    OrderState.from_address,
    or_f(F.text, F.location)
)
async def process_from_address(
        message: types.Message,
        state: FSMContext
):
    state_data = await state.get_data()
    to_address_data = state_data.get('to_address')
    city = None
    if to_address_data:
        city = to_address_data['address'].split(',')[0]

    try:
        from_address, cords = await get_message_address(message, city)
        from_lat, from_lon = cords
    except API2GisError as e:
        error_msg = str(e) if not message.location else (
            'Не получилось распознать ваш адрес по геопозиции(\n\n'
            '<em>Пожалуйста, напишите адрес вручную.</em>'
        )
        await message.answer(error_msg)
        return

    if not await validate_address_city(message, from_address):
        await message.answer(
            'К сожалению, мы не работаем в вашем регионе.',
            reply_markup=reply_keyboard_remove
        )
        await state.clear()
        return

    from_address_data = {
        'address': from_address,
        'lat': from_lat,
        'lon': from_lon
    }
    await state.update_data(from_address=from_address_data)

    if to_address_data:
        to_address = to_address_data['address']
        await send_order_message(message, from_address, to_address)
        return

    await message.answer(
        'Отправьте геолокацию назначения, или введите адрес вручную.\n\n'
        '<b><em>Примеры корректныx адресов:\n\n'
        f'<blockquote>{address_string}</blockquote></em></b>',
        reply_markup=reply_cancel_keyboard,
    )
    await state.set_state(OrderState.to_address)


@router.message(
    OrderState.to_address,
    or_f(F.text, F.location)
)
async def process_to_address(message: types.Message, state: FSMContext):
    await message.answer(
        '<em>Анализирую маршрут . . .</em>',
        reply_markup=reply_keyboard_remove,
    )

    state_data = await state.get_data()
    from_address = state_data['from_address']['address']
    city = from_address.split(',')[0]

    try:
        to_address, cords = await get_message_address(city, message)
        to_lat, to_lon = cords
        to_address_data = {
            'address': to_address,
            'lat': to_lat,
            'lon': to_lon
        }
        await state.update_data(to_address=to_address_data)
        await send_order_message(message, from_address, to_address)
    except API2GisError as e:
        error_msg = str(e) if not message.location else (
            'Не получилось распознать адрес по геопозиции(\n\n'
            '<em>Пожалуйста, напишите адрес вручную.</em>'
        )
        await message.answer(error_msg)
        return


@router.callback_query(F.data == 'edit_from_address')
async def edit_from_address_callback_handler(
        callback: types.CallbackQuery,
        state: FSMContext,
):
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(
        'Отправьте новый адрес отправки.'
    )
    await state.set_state(OrderState.from_address)


@router.callback_query(F.data == 'edit_to_address')
async def edit_to_address_callback_handler(
        callback: types.CallbackQuery,
        state: FSMContext,
):
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(
        'Отправьте новый адрес назначения.'
    )
    await state.set_state(OrderState.to_address)


@router.callback_query(F.data == 'create_order')
async def create_order_callback_handler(
        callback: types.CallbackQuery,
        state: FSMContext,
):
    state_data = await state.get_data()
    telegram_user = await TelegramUser.objects.aget(
        telegram_id=callback.from_user.id
    )

    from_address_data = state_data['from_address']
    to_address_data = state_data['to_address']
    order_data = {
        'type': state_data['type'],
        'telegram_user_id': telegram_user.id,

        'from_address': from_address_data['address'],
        'from_latitude': from_address_data['lat'],
        'from_longitude': from_address_data['lon'],

        'to_address': to_address_data['address'],
        'to_latitude': to_address_data['lat'],
        'to_longitude': to_address_data['lon'],
    }

    try:
       await Order.objects.acreate(**order_data)
    except API2GisError as e:
        await callback.message.edit_text(str(e))
        await state.clear()
        return

    await callback.message.delete()
    await callback.message.answer('<em>Поиск водителей . . .</em>')
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
        yookassa_payment_response = await create_payment(
            order_id=order_id,
            telegram_user_id=telegram_user.id
        )

        reply_markup = get_link_button_inline_keyboard(
            button_text='Оплатить 💳',
            url=yookassa_payment_response.confirmation.confirmation_url
        )
        points = yookassa_payment_response.metadata.get('points')
        await callback.message.edit_text(
            'Оплата поездки. После оплаты водитель направиться к вам.\n'
            f'Начислим {points} баллов.\n\n'
            '<b>ВАЖНО:</b> после оплаты обязательно нажмите '
            'на кнопку <b><em>"Вернуться на сайт"</em></b>, '
            'чтобы завершить оплату.',
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
    telegram_user = await TelegramUser.objects.aget(
        telegram_id=callback.from_user.id
    )
    yookassa_payment_response = await create_payment(
        order_id=order_id,
        telegram_user_id=telegram_user.id,
    )

    reply_markup = get_link_button_inline_keyboard(
        button_text='Оплатить 💳',
        url=yookassa_payment_response.confirmation.confirmation_url
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

    await state.update_data(
        obj_id=obj_id,
        obj_model=model,
    )
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

    model = state_data['obj_model']
    obj_id = state_data['obj_id']
    obj: Union[Order, Product] = await model.objects.aget(id=obj_id)

    payment_kwargs = {}
    if isinstance(obj, Order):
        obj_string = 'заказ'
        payment_kwargs['order_id'] = obj.id
        payment_text = \
            'Оплата поездки. После оплаты водитель направиться к вам.\n\n'
    else:
        obj_string = 'товар'
        payment_kwargs['product_id'] = obj.id
        payment_kwargs['metadata'] = {
            'address': state_data['address'],
            'phone_number': state_data['phone_number']
        }
        payment_text = \
            'Оплата товара. После оплаты к вам направиться доставка.\n\n'

    if points_count > obj.price / 2:
        await message.answer(
            f'Нельзя списать более 50% от стоимости {obj_string}а'
        )
        return

    payment_kwargs['price'] = obj.price - points_count
    telegram_user: TelegramUser = await TelegramUser.objects.aget(
        telegram_id=message.from_user.id
    )
    payment_kwargs['telegram_user_id'] = telegram_user.id

    try:
        telegram_user.points -= points_count
    except Exception:
        await message.answer('Произошла ошибка', )
        return
    finally:
        await telegram_user.asave()

    await message.answer('Баллы успешно списаны ✅')
    yookassa_payment_response = await create_payment(**payment_kwargs)
    await message.answer(
        payment_text +
        '<b>ВАЖНО:</b> после оплаты обязательно нажмите '
        'на кнопку <b><em>"Вернуться на сайт"</em></b>, '
        'чтобы завершить оплату.',
        reply_markup=InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(
                text="Оплатить 💳",
                url=yookassa_payment_response.confirmation.confirmation_url
            )
        ]]
    ),
    )
