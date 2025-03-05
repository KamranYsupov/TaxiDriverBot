from django.apps import AppConfig


class OrdersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'web.apps.orders'
    verbose_name = 'Аналитика'

    def ready(self):
        from . import signals
