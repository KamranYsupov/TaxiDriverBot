import uuid
from typing import Optional

from yookassa import Payment as YookassaPayment
from django.conf import settings
from yookassa.domain.response import PaymentResponse

from web.apps.orders.models import Payment


def create_yookassa_payment(
    db_payment_id: Payment.id,
    amount: float,
    metadata: Optional[dict] = None,
    description: Optional[str] = None
) -> PaymentResponse:
    idempotence_key = str(uuid.uuid4())

    payment = YookassaPayment.create({
        'amount': {
            'value': f'{amount:.2f}',
            'currency': 'RUB'
        },
        'confirmation': {
            'type': 'redirect',
            'return_url': f'{settings.BOT_LINK}?start=payment_{db_payment_id}'
        },
        'capture': True,
        'description': description,
        'metadata': metadata
    }, idempotence_key)

    return payment
