from asgiref.sync import async_to_sync

from celery import shared_task

from web.apps.orders.models import Order
from web.apps.orders.service import async_send_order_to_active_drivers


@shared_task(ignore_result=True)
def send_order_to_active_drivers_task(order_id: Order.id):
    return async_to_sync(async_send_order_to_active_drivers)(order_id)