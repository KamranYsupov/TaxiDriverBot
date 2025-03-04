from typing import Optional

from aiogram import Router, types, Bot, F
from yookassa.domain.response import PaymentResponse

from bot.keyboards.inline import get_inline_keyboard
from bot.utils.texts import get_order_info_message
from web.apps.orders.models import Order, Payment
from web.apps.products.models import Product
from web.apps.telegram_users.models import TelegramUser, TaxiDriver


async def successful_payment_handler(
        message: types.Message,
        payment: Payment,
        yookassa_payment: PaymentResponse,
):
    text = f'Платеж на сумму {payment.price} руб. прошел успешно ✅\n'


    if yookassa_payment.metadata.get('type') == 'order':
        text += 'Ожидайте водителя.'
        order: Order = await Order.objects.aget(id=payment.order_id)
        taxi_driver: TaxiDriver = await TaxiDriver.objects.aget(id=order.driver_id)
        order_info_message = get_order_info_message(order)

        await message.bot.send_message(
            chat_id=taxi_driver.telegram_id,
            text=(
                '<b>Заявка на заказ одобренна! Заказ активен ✅.</b>\n\n'
                + order_info_message
            ),
            reply_markup=get_inline_keyboard(
                buttons={'Завершить заказ': f'end_order_{order.id}'}
            )
        )

    await message.delete()
    await message.answer(text)

