import asyncio

from celery import shared_task
from django.conf import settings
from django.db.models import Q

from bot.utils.texts import get_order_info_message
from web.apps.orders.models import Order
from web.apps.telegram_users.models import TaxiDriver, TelegramUser
from web.services.telegram import telegram_service, async_telegram_service


@shared_task(ignore_result=True)
def send_order_to_active_drivers_task(order_id: Order.id):
    """"Задача для отправки заказа всем активным водителям"""
    order: Order = Order.objects.get(id=order_id)
    order_telegram_user: TelegramUser = TelegramUser.objects.get(id=order.telegram_user_id)

    active_drivers = TaxiDriver.objects.filter(
        ~Q(telegram_id=order_telegram_user.telegram_id),
        is_active=True
    )
    order_message = 'Поступил новый заказ!\n\n' + get_order_info_message(order)
    take_order_button = {'text': 'Взять ✅'}

    if not active_drivers.exists():
        take_order_button['callback_data'] = f'channel_take_order_{order.id}'
        telegram_service.send_message(
            chat_id=settings.PRIVATE_ORDERS_CHANNEL_ID,
            text=order_message,
            reply_markup={'inline_keyboard': [[take_order_button]]}
        )
        return

    for taxi_driver in active_drivers:
        take_order_button['callback_data'] = f'take_order_{order.id}'
        miss_order_button = {'text': 'Пропустить ❌', 'callback_data': f'miss_order_{order.id}'}
        inline_keyboard = [[take_order_button, miss_order_button]]

        asyncio.run(
            async_telegram_service.send_message(
                chat_id=taxi_driver.telegram_id,
                text=order_message,
                reply_markup={
                    'inline_keyboard': inline_keyboard}
            )
        )


@shared_task(ignore_result=True)
def send_order_private_channel_task(order_id: Order.id):
    """"Задача для отправки заказа в закрытый канал"""
    order = Order.objects.get(id=order_id)

    if order.driver_id:
        return

    order_message = 'Поступил новый заказ!\n\n' + get_order_info_message(order)
    inline_keyboard = [[
        {'text': 'Взять ✅', 'callback_data': f'channel_take_order_{order.id}'},
    ]]

    telegram_service.send_message(
        chat_id=settings.PRIVATE_ORDERS_CHANNEL_ID,
        text=order_message,
        reply_markup={'inline_keyboard': inline_keyboard}
    )

