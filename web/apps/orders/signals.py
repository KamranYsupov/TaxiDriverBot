from django.db.models.signals import post_save
from django.dispatch import receiver

from web.apps.orders.models import Order
from web.apps.orders.tasks import send_order_to_active_drivers_task


@receiver(post_save, sender=Order)
def order_post_save(sender, instance, created, **kwargs):
    if created and instance.driver is None:
        send_order_to_active_drivers_task(order_id=instance.id)

