from typing import Optional

from asgiref.sync import sync_to_async
from django.db import transaction
from yookassa.domain.response import PaymentResponse

from web.apps.orders.models import Order, OrderPriceSettings, Payment, PointsSettings
from web.apps.products.models import Product
from web.apps.telegram_users.models import TelegramUser
from web.services.yookassa import create_yookassa_payment


async def create_order_payment(
        order_id: Order.id,
        telegram_user_id: TelegramUser.id,
        price: Optional[Product.id] = None,
        metadata: Optional[dict] = None,
) -> PaymentResponse:
    return await create_payment(
        price=price,
        telegram_user_id=telegram_user_id,
        order_id=order_id,
        metadata=metadata,
    )


@sync_to_async
def create_payment(
        telegram_user_id: TelegramUser.id,
        price: Optional[Order.id] = None,
        order_id: Optional[Order.id] = None,
        product_id: Optional[Product.id] = None,
        metadata: Optional[dict] = None,
) -> PaymentResponse | None:
    payment = Payment(
        price=price,
        telegram_user_id=telegram_user_id
    )
    payment_description = 'Оплата '
    metadata = {} if not metadata else metadata

    if order_id:
        obj: Order = Order.objects.get(id=order_id)
        payment.order = obj
        payment.type = obj.type
        payment_description += 'заказа'
        order_price_settings = OrderPriceSettings.load()
        points = int((obj.price - order_price_settings.default_order_price) / 2)
        metadata['type'] = 'order'

    elif product_id:
        obj: Product = Product.objects.get(id=product_id)
        payment.product = obj
        payment.type = Payment.PRODUCT
        payment_description += 'товара'

        points = int(
            obj.price * PointsSettings.load().points_percent_for_product / 100
        )
        metadata['type'] = 'product'

    else:
        return None

    payment.price = price if price else obj.price
    metadata['points'] = points

    with transaction.atomic():
        payment.save()
        yookassa_payment_response = create_yookassa_payment(
            db_payment_id=payment.id,
            amount=payment.price,
            description=payment_description,
            metadata=metadata,
        )

        payment.yookassa_payment_id = yookassa_payment_response.id
        payment.save()

    return yookassa_payment_response
