from copy import copy

from celery.utils.functional import pass1
from django.db import models
from django.utils.translation import gettext_lazy as _

from web.apps.telegram_users.models import TaxiDriver
from web.db.model_mixins import (
    AsyncBaseModel,
    TariffMixin,
    TimestampMixin,
    PriceMixin
)
from web.services.api_2gis import api_2gis_service


class OrderType:
    TAXI = 'Taxi'
    DELIVERY = 'Delivery'

    CHOICES = [
        (TAXI, _('Такси')),
        (DELIVERY, _('Доставка')),
    ]


class Order(AsyncBaseModel, TariffMixin, PriceMixin, TimestampMixin):
    """Модель заказа"""
    from_address = models.CharField(_('Откуда'), max_length=150)
    from_latitude = models.FloatField(_('Широта '))
    from_longitude = models.FloatField(_('Долгота'))

    to_address = models.CharField(_('Куда'), max_length=150)
    to_latitude = models.FloatField(_('Широта'))
    to_longitude = models.FloatField(_('Долгота'))

    type = models.CharField(
        _('Тип поездки'),
        choices=OrderType.CHOICES,
        default=OrderType.TAXI,
        max_length=15,
    )
    travel_time_minutes = models.PositiveIntegerField(_('Примерное время поезки'))

    current_active_drivers_count = models.PositiveIntegerField(
        _('Количесто активных водителей в момент создания заказа'),
        editable=False
    )
    miss_drivers_count = models.PositiveIntegerField(
        _('Количесто водителей, отклонивших заказ'),
        default=0
    )

    telegram_user = models.ForeignKey(
        'telegram_users.TelegramUser',
        related_name='orders',
        on_delete=models.SET_NULL,
        verbose_name=_('Заказчик'),
        null=True,
    )
    driver = models.ForeignKey(
        'telegram_users.TaxiDriver',
        related_name='orders',
        on_delete=models.SET_NULL,
        verbose_name=_('Водитель'),
        default=None,
        null=True,
    )


    updated_at = None # Исключаем updated_at

    class Meta:
        verbose_name = _('Заказ')
        verbose_name_plural = _('Заказы')

    def __str__(self):
        return f'{self.type}: {self.from_address} - {self.to_address}'

    def save(self, *args, **kwargs):
        _, travel_time_seconds = api_2gis_service.get_route_distance_and_duration(
            from_lat=self.from_latitude,
            from_lon=self.from_longitude,
            to_lat=self.to_latitude,
            to_lon=self.to_longitude,
        )
        self.travel_time_minutes = round(travel_time_seconds / 60)
        self.price = 100.0
        self.current_active_drivers_count = TaxiDriver.objects.filter(is_active=True).count()
        super().save(*args, **kwargs)


class Payment(AsyncBaseModel, PriceMixin, TimestampMixin):
    """Модель оплаты"""
    PRODUCT = 'Product'

    TYPE_CHOICES = copy(OrderType.CHOICES)
    TYPE_CHOICES.append((PRODUCT, _('Товар')))

    type = models.CharField(
        _('Тип поездки'),
        choices=TYPE_CHOICES,
        max_length=15,
    )

    order = models.OneToOneField(
        'orders.Order',
        related_name='payment',
        on_delete=models.CASCADE,
        verbose_name=_('Заказ'),
        blank=True,
        null=True,
        default=None,
    )
    product = models.OneToOneField(
        'products.Product',
        related_name='payment',
        on_delete=models.CASCADE,
        verbose_name=_('Товар'),
        blank=True,
        null=True,
        default=None,
    )

    telegram_user = models.ForeignKey(
        'telegram_users.TelegramUser',
        related_name='payments',
        on_delete=models.SET_NULL,
        verbose_name=_('Пользователь'),
        null=True,
    )

    updated_at = None # Исключаем updated_at

    class Meta:
        verbose_name = _('Оплата')
        verbose_name_plural = _('Оплаты')

    def __str__(self):
        return f'{self.type}: {self.price}р.'


