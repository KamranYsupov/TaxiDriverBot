from typing import Optional

from aiogram import Router, types, F
from asgiref.sync import sync_to_async

from bot.keyboards.inline import (
    get_inline_keyboard,
    get_inline_review_driver_keyboard
)
from bot.utils.bot import edit_text_or_answer
from bot.utils.texts import get_order_info_message
from web.apps.orders.models import Order
from web.apps.telegram_users.models import (
    TelegramUser,
    TaxiDriver,
    Car,
    TariffDriverRequest
)

router = Router()


async def is_car_approved_handler(
        callback: types.CallbackQuery,
        car: Optional[Car] = None
):
    if not car:
        taxi_driver: TaxiDriver = (await TaxiDriver.objects.afilter(
            telegram_id=callback.from_user.id,
            select_relations=('car',)
        ))[0]
        car = taxi_driver.car

    if not car or car.status == Car.DISAPPROVED:
        text = 'Сначала зарегестрируйте авто'
    elif car.status == Car.WAITING:
        text = 'Ожидайте. Авто на проверке.'
    else:
        return True

    await callback.message.edit_text(
        text,
        reply_markup=get_inline_keyboard(
            buttons={'Назад 🔙': 'menu_driver'}
        )
    )


async def is_tariff_request_approved_handler(
        callback: types.CallbackQuery,
        tariff_request: TariffDriverRequest
):
    if tariff_request.status == Car.APPROVED:
        return True

    if tariff_request.status == Car.WAITING:
        text = 'Ожидайте. Авто на проверке.'
    else:
        text = 'Сначала зарегестрируйте авто'

    await callback.message.edit_text(
        text,
        reply_markup=get_inline_keyboard(
            buttons={'Назад 🔙': 'menu_driver'}
        )
    )


@router.callback_query(F.data == 'is_active')
async def is_active_callback_handler(callback: types.CallbackQuery):
    taxi_driver: TaxiDriver = (await TaxiDriver.objects.afilter(
        telegram_id=callback.from_user.id,
        select_relations=('car',)
    ))[0]
    car = taxi_driver.car

    if not await is_car_approved_handler(callback, car):
        return

    button_text = 'Включить ✅' if not taxi_driver.is_active else 'Выключить ❌'
    message_text = (
        'Смена: '
        f'<b>{"включена ✅" if taxi_driver.is_active else "выключена ❌"}</b>'
    )
    buttons = {
        button_text: 'driver_change-is_active',
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
    if change_field_name not in ('is_active', ):
        return

    taxi_driver: TaxiDriver = await TaxiDriver.objects.aget(
        telegram_id=callback.from_user.id,
    )
    change_field_value = getattr(taxi_driver, change_field_name)  # Достаём значение нужного поля
    setattr(taxi_driver, change_field_name, not change_field_value)  # Изменяем значение нужного поля на противоположное

    await taxi_driver.asave()

    if change_field_name == 'is_active':
        await is_active_callback_handler(callback)


@router.callback_query(F.data == 'driver_tariff')
async def driver_tariff_callback_handler(callback: types.CallbackQuery):
    taxi_driver: TaxiDriver = await TaxiDriver.objects.aget(
        telegram_id=callback.from_user.id,
    )
    if not await is_car_approved_handler(callback):
        return

    buttons = {}
    sizes = (1, ) * (len(TaxiDriver.TARIFF_CHOICES) + 1)

    for tariff in TaxiDriver.TARIFF_CHOICES:
        button_text = tariff[-1]
        if taxi_driver.tariff == tariff[0]:
            button_text += ' ✅'

        buttons[button_text] = f'request_tariff_{tariff[0]}'


    buttons.update({'Назад 🔙': 'menu_driver',})
    await callback.message.edit_text(
        'Выберите тариф.',
        reply_markup=get_inline_keyboard(
            buttons=buttons,
            sizes=sizes
        )
    )


@router.callback_query(F.data.startswith('request_tariff_'))
async def request_tariff_callback_handler(callback: types.CallbackQuery):
    tariff = callback.data.split('_')[-1]
    taxi_driver: TaxiDriver = await TaxiDriver.objects.aget(
        telegram_id=callback.from_user.id,
    )
    if taxi_driver.tariff == tariff:
        return

    tariff_request_kwargs = dict(
        driver=taxi_driver,
        tariff=tariff,
        status=TariffDriverRequest.WAITING,
    )
    tariff_requests = await TariffDriverRequest.objects.afilter(**tariff_request_kwargs)

    if tariff_requests:
        text = 'Вы уже отправили запрос. Ожидайте ответа администрации.'
    else:
        await TariffDriverRequest.objects.acreate(**tariff_request_kwargs)
        text = '✅ Ваша заявка успешно отправлена! Ожидайте ответа администрации.'


    await callback.message.edit_text(
        text,
        reply_markup=get_inline_keyboard(buttons={'Назад 🔙': 'menu_driver'})
    )


async def driver_take_order_handler(
        callback: types.CallbackQuery,
        from_channel: bool = False
):
    order_id = callback.data.split('_')[-1]
    order = (await Order.objects.afilter(
        id=order_id,
        select_relations=('telegram_user',)
    ))[0]

    taxi_driver: TaxiDriver = (await TaxiDriver.objects.afilter(
        telegram_id=callback.from_user.id,
        select_relations=('car',)
    ))[0]

    if order.driver_id == taxi_driver.id:
        await callback.answer('Вы уже взяли заказ')
        return

    if order.driver_id:
        text = 'Извини, но кто-то успел принять заказ до тебя'
        await callback.answer(text) if from_channel \
            else callback.message.edit_text(text, reply_markup=None)
        return

    driver_rating = f'{taxi_driver.rating} ⭐️' if taxi_driver.rating else 'нет оценки'
    order_info_message = (
        f'<b>Водитель</b>: <em>{taxi_driver.full_name}</em> '
        f'<b>({driver_rating})</b>\n\n'
        f'<b>Стоимость поездки</b>: <em>{order.price} руб.</em>\n'
        f'<b>Примерное время поездки</b>: <em>{order.travel_time_minutes} минут</em>\n'
        f'<b>Машина</b>: <em>{taxi_driver.car.name}</em>\n'
        f'<b>Номер</b>: <em>{taxi_driver.car.gos_number}</em>\n'
    )

    await callback.bot.send_message(
        chat_id=order.telegram_user.telegram_id,
        text=order_info_message,
        reply_markup=get_inline_keyboard(
            buttons={'Выбрать ☑️': f'accept_order_{order.id}_{taxi_driver.id}'}
        )
    )

    text = 'Заявка отправлена пользователю ✅\n\n Ожидайте ответа.'

    if not from_channel:
        await callback.message.edit_text(
            text=text,
            reply_markup=None,
        )
        return

    await callback.bot.send_message(
        chat_id=taxi_driver.telegram_id,
        text=text,
    )


@router.callback_query(F.data.startswith('take_order_'))
async def driver_take_order_callback_handler(callback: types.CallbackQuery):
    await driver_take_order_handler(callback, from_channel=False)


@router.callback_query(F.data.startswith('channel_take_order_'))
async def driver_channel_take_order_callback_handler(callback: types.CallbackQuery):
    await driver_take_order_handler(callback, from_channel=True)


@router.callback_query(F.data.startswith('miss_order_'))
async def driver_miss_order_callback_handler(callback: types.CallbackQuery):
    await callback.message.edit_text(
        'Заказ отклонён.',
        reply_markup=None,
    )


@router.callback_query(F.data.startswith('end_order'))
async def end_order_callback_handler(callback: types.CallbackQuery):
    order_id = callback.data.split('_')[-1]

    await callback.message.edit_text(
        '<b>Вы уверены?</b>',
        reply_markup=get_inline_keyboard(
            buttons={
                'Да': f'confirm_end_order_{order_id}',
                'Нет': f'cancel_end_order_{order_id}'
            }
        )
    )


@router.callback_query(F.data.startswith('cancel_end_order_'))
async def cancel_end_order_callback_handler(callback: types.CallbackQuery):
    order_id = callback.data.split('_')[-1]
    order: Order = await Order.objects.aget(id=order_id)
    order_info_message = get_order_info_message(order)

    await callback.message.edit_text(
        order_info_message,
        reply_markup=get_inline_keyboard(
            buttons={'Завершить заказ': f'end_order_{order.id}'}
        )
    )


@router.callback_query(F.data.startswith('confirm_end_order_'))
async def confirm_end_order_callback_handler(callback: types.CallbackQuery):
    order_id = callback.data.split('_')[-1]
    order: Order = await Order.objects.aget(id=order_id)
    taxi_driver: TaxiDriver = await TaxiDriver.objects.aget(id=order.driver_id)
    order_telegram_user: TelegramUser = await TelegramUser.objects.aget(
        id=order.telegram_user_id
    )

    await callback.message.edit_text(
        'Заказ завершен ✅',
        reply_markup=None,
    )

    await callback.bot.send_message(
        chat_id=order_telegram_user.telegram_id,
        text='Пожалуйста, оцените водителя',
        reply_markup=get_inline_review_driver_keyboard(
            driver_id=taxi_driver.id
        )
    )





