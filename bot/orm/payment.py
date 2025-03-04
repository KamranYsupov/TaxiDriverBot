from typing import Optional

from asgiref.sync import sync_to_async
from django.db import transaction
from yookassa.domain.response import PaymentResponse

from web.apps.orders.models import Order, OrderPriceSettings, Payment
from web.apps.telegram_users.models import TelegramUser
from web.services.yookassa import create_yookassa_payment


@sync_to_async
def create_order_payment(
        order_id: Order.id,
        price: Optional[float] = None,
) -> PaymentResponse:
    order: Order = Order.objects.get(id=order_id)

    order_price_settings = OrderPriceSettings.load()
    points = int((order.price - order_price_settings.default_order_price) / 2)
    payment_price = order.price if not price else price

    with transaction.atomic():
        payment = Payment.objects.create(
            type=order.type,
            order=order,
            telegram_user_id=order.telegram_user_id,
            price=payment_price
        )
        yookassa_payment_response = create_yookassa_payment(
            db_payment_id=payment.id,
            amount=payment_price,
            description='Оплата заказа',
            metadata={
                'type': 'order',
                'points': points,
            }
        )

        payment.yookassa_payment_id = yookassa_payment_response.id
        payment.save()

    return yookassa_payment_response
