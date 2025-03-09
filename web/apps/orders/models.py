from copy import copy

from django.core.validators import MaxValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from web.apps.telegram_users.models import TelegramUser
from web.db.model_mixins import (
    AsyncBaseModel,
    TariffMixin,
    TimestampMixin,
    PriceMixin,
    SingletonModel
)
from web.db.models import PriceField
from web.services.api_2gis import api_2gis_service


class Order(AsyncBaseModel, TariffMixin, PriceMixin, TimestampMixin):
    """Модель заказа"""
    TAXI = 'Taxi'
    DELIVERY = 'Delivery'

    TYPE_CHOICES = [
        (TAXI, _('Такси')),
        (DELIVERY, _('Доставка')),
    ]

    from_address = models.CharField(_('Откуда'), max_length=150)
    from_latitude = models.FloatField(_('Широта'))
    from_longitude = models.FloatField(_('Долгота'))

    to_address = models.CharField(_('Куда'), max_length=150)
    to_latitude = models.FloatField(_('Широта'))
    to_longitude = models.FloatField(_('Долгота'))

    type = models.CharField(
        _('Тип поездки'),
        choices=TYPE_CHOICES,
        default=TAXI,
        max_length=15,
    )
    travel_length_km = models.FloatField(_('Длина пути в км'), validators=[MaxValueValidator])
    travel_time_minutes = models.PositiveIntegerField(_('Примерное время поездки в минутах'))

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
        return f'{self.from_address} - {self.to_address}'

    def save(self, *args, **kwargs):
        if not self._state.adding:
            super().save(*args, **kwargs)
            return

        travel_length_meters, travel_time_seconds = api_2gis_service.get_route_distance_and_duration(
            from_lat=self.from_latitude,
            from_lon=self.from_longitude,
            to_lat=self.to_latitude,
            to_lon=self.to_longitude,
        )
        self.travel_length_km = travel_length_meters / 1000
        self.travel_time_minutes = round(travel_time_seconds / 60)
        self.price = self.calculate_price()

        super().save(*args, **kwargs)

    def calculate_price(self):
        price_settings: OrderPriceSettings = OrderPriceSettings.load()
        default_order_price = price_settings.default_order_price

        if self.telegram_user.tariff == TelegramUser.URGENT:
            default_order_price += default_order_price * 0.27 # + 27%

        price = int(
            default_order_price + (
                price_settings.price_for_km * self.travel_length_km +
                price_settings.price_for_travel_minute * self.travel_time_minutes
            )
        )
        return price


class Payment(AsyncBaseModel, PriceMixin, TimestampMixin):
    """Модель оплаты"""
    TAXI = 'Taxi'
    DELIVERY = 'Delivery'
    PRODUCT = 'Product'

    TYPE_CHOICES = [
        (TAXI, _('Такси')),
        (DELIVERY, _('Доставка')),
        (PRODUCT, _('Продукт'))
    ]

    NOT_PAID = 'Not paid'
    PAID = 'Paid'

    STATUS_CHOICES = (
        (NOT_PAID, _('Не оплачен')),
        (PAID, _('Оплачен'))
    )

    yookassa_payment_id = models.CharField(
        _('Код платежа yookassa'),
        db_index=True,
        editable=False,
        unique=True,
        max_length=40,
    )
    type = models.CharField(
        _('Тип оплаты'),
        choices=TYPE_CHOICES,
        max_length=15,
    )
    status = models.CharField(
        _('Статус'),
        choices=STATUS_CHOICES,
        max_length=8,
        default=NOT_PAID,
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
    product = models.ForeignKey(
        'products.Product',
        related_name='payments',
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
        return f'{self.telegram_user}: {self.price}р.'


class OrderPriceSettings(AsyncBaseModel, SingletonModel):
    """Singelton модель настроек для расчета стоимости заказа"""

    default_order_price = PriceField(
        _('Стоимость подачи'),
        default=0
    )
    price_for_km = PriceField(
        _('Стоимость за километр'),
        default=0
    )
    price_for_travel_minute = PriceField(
        _('Стоимость за минуту пути'),
        default=0
    )

    class Meta:
        verbose_name = _('Настройки расчета стоимости заказа')
        verbose_name_plural = verbose_name

    def __str__(self):
        return ''


class PointsSettings(AsyncBaseModel, SingletonModel):
    """Singelton модель настроек начисления бонусов"""

    points_percent_for_product = models.PositiveIntegerField(
        _('Процент начисления бонусов от цены товара'),
        default=0
    )

    class Meta:
        verbose_name = _('Настройки начисления бонусов')
        verbose_name_plural = verbose_name

    def __str__(self):
        return ''