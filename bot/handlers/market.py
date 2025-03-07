import os
from typing import List

from aiogram import Router, types, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext

from bot.handlers.order import validate_address_city
from bot.keyboards.inline import (
    get_inline_keyboard,
    inline_driver_keyboard,
    inline_user_keyboard,
    get_link_button_inline_keyboard
)
from bot.keyboards.reply import reply_location_keyboard, reply_contact_keyboard, reply_keyboard_remove
from bot.orm.payment import create_product_payment
from bot.states.product import ProductState
from bot.utils.pagination import Paginator, get_pagination_buttons
from web.apps.products.models import Product

from web.apps.telegram_users.models import TelegramUser
from web.services.api_2gis import api_2gis_service


router = Router()

@router.callback_query(F.data.startswith('market_'))
async def marker_callback_handler(
    callback: types.CallbackQuery,
):
    page_number = int(callback.data.split('_')[-1])
    per_page = 10
    products: List[Product] = await Product.objects.a_all()
    paginator = Paginator(
        array=products,
        page_number=page_number,
        per_page=per_page,
    )

    buttons = {
        product.name: f'product_{product.id}_{page_number}'
        for product in paginator.get_page()
    }
    pagination_buttons = get_pagination_buttons(
        paginator, prefix='market_'
    )
    sizes = (1,) * per_page

    if not pagination_buttons:
        pass
    elif len(pagination_buttons.items()) == 1:
        sizes += (1, 1)
    else:
        sizes += (2, 1)

    buttons.update(pagination_buttons)
    buttons['Назад 🔙'] = 'menu_user'

    await callback.message.edit_text(
        'Выберите товар.',
        reply_markup=get_inline_keyboard(
            buttons=buttons,
            sizes=sizes,
        ),
    )


@router.callback_query(F.data.startswith('product_'))
async def product_info_callback_handler(
    callback: types.CallbackQuery,
    state: FSMContext,
):
    product_id = callback.data.split('_')[-2]
    marker_page_number = int(callback.data.split('_')[-1])

    product = await Product.objects.aget(id=product_id)
    text = (
        f'<b>{product.name}</b>\n\n'
        f'<em>{product.description}</em>\n\n'
        f'<b>Цена:</b> <em>{int(product.price)} рублей</em>'
    )

    buttons = {
        'Заказать 🛒': f'buy_{product.id}',
        'Назад 🔙': f'market_{marker_page_number}',
    }

    await callback.message.edit_text(
        text,
        reply_markup=get_inline_keyboard(
            buttons=buttons,
            sizes=(1, 1),
        ),
    )


@router.callback_query(F.data.startswith('buy_'))
async def buy_product_callback_handler(
    callback: types.CallbackQuery,
    state: FSMContext,
):
    product_id = callback.data.split('_')[-1]
    await state.update_data(product_id=product_id)

    await callback.message.edit_reply_markup(
        reply_markup=None
    )
    await callback.message.answer(
        'Нажмите на кнопку <b>"Отправить геолокацию 🏬"</b>'
        'чтобы отправить ваш адресс.',
        reply_markup=reply_location_keyboard
    )
    await state.set_state(ProductState.address)


@router.message(ProductState.address, F.text)
async def process_address_message_handler(
    message: types.Message,
    state: FSMContext
):
    location = message.location
    lat, lon = location.latitude, location.longitude
    address = api_2gis_service.get_address(lat, lon)
    if not await validate_address_city(message, address):
        await state.clear()
        return

    state_data = await state.update_data(address=address)
    product_id = state_data['product_id']

    await message.answer(
        f'Ваш адресс - <b>{address}</b>?',
        reply_markup=get_inline_keyboard(
            buttons={'Все верно ✅': f'confirm_address'}
        )
    )


@router.callback_query(F.data == 'confirm_address')
async def confirm_address_callback_handler(
        callback: types.CallbackQuery,
        state: FSMContext
):
    await callback.message.edit_reply_markup(
        reply_markup=None
    )
    await state.set_state(ProductState.phone_number)
    await callback.message.answer(
        'Для оформления доставки нажмите на кнопку '
        '<b>"Отправить номер телефона 📲"</b>, чтобы его отправить',
        reply_markup=reply_contact_keyboard
    )


@router.message(F.contact, ProductState.phone_number)
async def process_phone_number_message_handler(
        message: types.Message,
        state: FSMContext
):
    state_data = await state.update_data(
        phone_number=message.contact.phone_number
    )
    product_id = state_data['product_id']

    telegram_user = await TelegramUser.objects.aget(
        telegram_id=message.from_user.id
    )
    await message.answer(
        '<b>Оплата:</b>',
        reply_markup=reply_keyboard_remove
    )

    if not telegram_user.points:
        state_data = await state.get_data()

        yookassa_payment_response = await create_product_payment(
            product_id=product_id,
            telegram_user_id=telegram_user.id,
            metadata={
                'address': state_data['address'],
                'phone_number': state_data['phone_number']
            }
        )

        reply_markup = get_link_button_inline_keyboard(
            button_text='Оплатить 💳',
            url=yookassa_payment_response.confirmation.confirmation_url
        )
        points = yookassa_payment_response.metadata.get('points')
        await message.answer(
            f'Начислим {points} баллов.\n\n'
            '<b>ВАЖНО:</b> после оплаты обязательно нажмите '
            'на кнопку <b><em>"Вернуться на сайт"</em></b>, '
            'чтобы завершить оплату.',
            reply_markup=reply_markup,
        )
        return

    await message.answer(
        f'Хотите списать баллы?\n\n'
        f'<em>Баллы оплачивают до 50% от цены товара</em>.',
        reply_markup=get_inline_keyboard(
            buttons={
                f'Списать баллы ({telegram_user.points}) 💸': \
                    f'write_off_points_product_{product_id}',
                'Оплатить полностью 💳': f'send_payment_product_{product_id}',
            }
        )
    )


@router.callback_query(F.data.startswith('send_payment_product_'))
async def send_payment_product_callback_handler(
    callback: types.CallbackQuery,
    state: FSMContext
):
    product_id = callback.data.split('_')[-1]
    telegram_user = await TelegramUser.objects.aget(
        telegram_id=callback.from_user.id
    )
    state_data = await state.get_data()

    yookassa_payment_response = await create_product_payment(
        product_id=product_id,
        telegram_user_id=telegram_user.id,
        metadata={
            'address': state_data['address'],
            'phone_number': state_data['phone_number']
        }
    )

    reply_markup = get_link_button_inline_keyboard(
        button_text='Оплатить 💳',
        url=yookassa_payment_response.confirmation.confirmation_url
    )
    points = yookassa_payment_response.metadata.get('points')
    await callback.message.edit_text(
        'Оплата товара.\n'
            f'Начислим {points} баллов.\n\n'
            '<b>ВАЖНО:</b> после оплаты обязательно нажмите '
            'на кнопку <b><em>"Вернуться на сайт"</em></b>, '
            'чтобы завершить оплату.',
        reply_markup=reply_markup,
    )




