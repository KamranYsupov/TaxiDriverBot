from datetime import timedelta
from typing import Sequence

from celery import shared_task
from django.conf import settings
from django.utils import timezone

from web.apps.telegram_users.models import TaxiDriver, TelegramUser


@shared_task(ignore_result=True)
def reset_to_zero_points_task():
    now = timezone.now()
    reset_to_zero_date = (
            now + timedelta(minutes=5)
    ).date()
    telegram_users = TelegramUser.objects.all()
    updated_users = []

    for user in telegram_users:
        if user.last_add_points_date < reset_to_zero_date:
            continue

        user.points = 0
        updated_users.append(user)

    TelegramUser.objects.bulk_update(updated_users, ['points'])
