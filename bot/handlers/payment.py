from typing import Optional

from aiogram import Router, types, Bot, F

from bot.keyboards.inline import get_inline_keyboard
from bot.utils.texts import get_order_info_message
from web.apps.orders.models import Order, Payment
from web.apps.products.models import Product
from web.apps.telegram_users.models import TelegramUser, TaxiDriver

router = Router()

@router.pre_checkout_query()
async def pre_checkout(pre_checkout_query: types.PreCheckoutQuery, bot: Bot):
    invoice_payload = pre_checkout_query.invoice_payload
    obj_id = invoice_payload.split('_')[-1]
    obj = None

    if invoice_payload.startswith('order_'):
        obj: Optional[Order] = await Order.objects.aget(id=obj_id)
    elif invoice_payload.startswith('product_'):
        obj: Optional[Product] = await Product.objects.aget(id=obj_id)

    if obj:
        await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)
        return

    await bot.answer_pre_checkout_query(
        pre_checkout_query.id,
        ok=False,
        error_message='Ошибка в данных платежа'
    )


@router.message(F.successful_payment)
async def process_successful_payment(message: types.Message):
    invoice_payload = message.successful_payment.invoice_payload
    obj_id = invoice_payload.split('_')[-1]
    message_text = (
        f'Платеж на сумму {message.successful_payment.total_amount // 100} '
        f'руб. прошел успешно ✅\n'
    )
    payment_data = {}
    telegram_user: TelegramUser = await TelegramUser.objects.aget(
        telegram_id=message.from_user.id
    )
    payment_data['telegram_user'] = telegram_user

    if invoice_payload.startswith('order_'):
        obj: Order = await Order.objects.aget(id=obj_id)
        payment_data['order'] = obj
        payment_data['type'] = obj.type
        message_text += 'Ожидайте водителя.'
    elif invoice_payload.startswith('product_'):
        obj: Product = await Product.objects.aget(id=obj_id)
        payment_data['product'] = obj
        payment_data['type'] = Payment.PRODUCT
    else:
        await message.answer('Неверный платёж!')
        return

    payment_data['price'] = obj.price


    payment = await Payment.objects.acreate(**payment_data)
    await message.delete()
    await message.answer(message_text)

    if payment.order:
        taxi_driver: TaxiDriver = await TaxiDriver.objects.aget(id=payment.order.driver_id)
        order_info_message = get_order_info_message(payment.order)

        await message.bot.send_message(
            chat_id=taxi_driver.telegram_id,
            text=(
                '<b>Заявка на заказ одобренна! Заказ активен ✅.</b>\n\n'
                + order_info_message
            ),
            reply_markup=get_inline_keyboard(
                buttons={
                    'Завершить заказ': f'end_order_{payment.order.id}'
                }
            )
        )
