from typing import List

from asgiref.sync import sync_to_async
from django.conf import settings
from django.db.models import Q

from web.services.telegram import async_telegram_service
from web.apps.telegram_users.models import TaxiDriver, TelegramUser
from web.apps.orders.models import Order, OrderType


async def async_send_order_to_active_drivers(order_id: Order.id):
    """Функция для асинхонной отправки заказа всем активным водителям"""

    order: Order = await Order.objects.aget(id=order_id)
    order_telegram_user: TelegramUser = await TelegramUser.objects.aget(id=order.telegram_user_id)

    active_drivers = (
        await sync_to_async(TaxiDriver.objects.filter)(
            ~Q(telegram_id=order_telegram_user.telegram_id),
            is_active=True
        )
    )

    order_type = 'Такси 🚕' if order.type == OrderType.TAXI else 'Доставка 📦'
    order_message = (
        'Поступил новый заказ!\n\n'
        f'<b>Тип:</b> <em>{order_type}</em>\n'
        f'<b>Откуда:</b> <em>{order.from_address}</em>\n'
        f'<b>Куда:</b> <em>{order.to_address}</em>\n\n'
        f'<b>Cтоимость:</b> <em>{order.price} руб.</em>\n'
    )

    if not await active_drivers.aexists():
        inline_keyboard = [[
            {'text': 'Взять ✅', 'url': f'{settings.BOT_LINK}?start={order.id}'},
        ]]

        await async_telegram_service.send_message(
            chat_id=settings.PRIVATE_ORDERS_CHANNEL_ID,
            text=order_message,
            reply_markup={'inline_keyboard': inline_keyboard}
        )

        return

    async for taxi_driver in active_drivers:
        inline_keyboard = [[
            {'text': 'Взять ✅', 'callback_data': f'take_order_{order.id}'},
            {'text': 'Пропустить ❌', 'callback_data': f'miss_order_{order.id}'}
        ]]

        await async_telegram_service.send_message(
            chat_id=taxi_driver.telegram_id,
            text=order_message,
            reply_markup={'inline_keyboard': inline_keyboard}
        )


