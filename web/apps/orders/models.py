from copy import copy

from django.db import models
from django.utils.translation import gettext_lazy as _
from web.db.model_mixins import (
    AsyncBaseModel,
    TariffMixin,
    TimestampMixin,
    PriceMixin
)


class OrderType:
    TAXI = 'Taxi'
    DELIVERY = 'Delivery'

    CHOICES = [
        (TAXI, _('Такси')),
        (DELIVERY, _('Доставка')),
    ]


class Order(AsyncBaseModel, TariffMixin, PriceMixin, TimestampMixin):
    """Модель заказа"""
    from_address = models.CharField(_('Откуда'), max_length=200)
    to_address = models.CharField(_('Куда'), max_length=200)
    type = models.CharField(
        _('Тип поездки'),
        choices=OrderType.CHOICES,
        default=OrderType.TAXI,
        max_length=15,
    )
    travel_time_minutes = models.PositiveIntegerField(_('Примерное время поезки'))

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
        null=True,
    )


    updated_at = None # Исключаем updated_at

    class Meta:
        verbose_name = _('Заказ')
        verbose_name_plural = _('Заказы')

    def __str__(self):
        return f'{self.type}: {self.from_address} - {self.to_address}'


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


