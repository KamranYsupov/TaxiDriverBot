import os

from celery import Celery
from celery.schedules import crontab

from . import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'web.core.settings')

app = Celery('app')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'reset_to_zero_points_task':{
        'task': 'web.apps.telegram_users.tasks.reset_to_zero_points_task',
        'schedule': crontab(hour='0'),
    },
}
app.conf.timezone = 'Europe/Moscow'
