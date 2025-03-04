from datetime import timedelta

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from web.apps.orders.models import Order
from web.apps.orders.tasks import (
    send_order_to_active_drivers_task,
    send_order_private_channel_task,
)


@receiver(post_save, sender=Order)
def order_post_save(sender, instance: Order, created: bool, **kwargs):
    if created and instance.driver is None:
        send_order_to_active_drivers_task.delay(instance.id)
        send_order_private_channel_task.apply_async(
            args=(instance.id, ),
            eta=timezone.now() + timedelta(
                minutes=settings.SEND_ORDER_TO_CHANNEL_MINUTES_INTERVAL
            ),
        )


