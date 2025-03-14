from datetime import date

from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from web.db.model_mixins import (
    AsyncBaseModel,
    AbstractTelegramUser,
    TariffMixin,
    RequestStatusMixin
)
from web.services.telegram import telegram_service


class TelegramUser(AbstractTelegramUser, TariffMixin):
    """Модель telegram пользователя(заказчика)"""
    points = models.PositiveBigIntegerField(_('Баллы'), default=200)
    last_add_points_date = models.DateField(
        _('Дата последнего получения бонусов'),
        default=date.today
    )

    class Meta:
        verbose_name = _('пользователь')
        verbose_name_plural = _('Telegram пользователи')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__points = self.points

    def __str__(self):
        return self.username if self.username else f'Пользователь {self.id}'

    def save(self, *args, **kwargs):
        self._update_last_add_points_date()
        super().save(*args, **kwargs)

    async def asave(self, *args, **kwargs):
        self._update_last_add_points_date()
        await super().asave(*args, **kwargs)

    def _update_last_add_points_date(self):
        if self.points > self.__points:
            self.last_add_points_date = timezone.now().date()


class Car(AsyncBaseModel, RequestStatusMixin):
    """Модель авто"""

    name = models.CharField(_('Название'), max_length=150)
    gos_number = models.CharField(_('Государственный номер'), max_length=20)
    vin = models.CharField(_('ВИН'), max_length=20)

    front_photo = models.ImageField(_('Фото спереди'), upload_to='cars/fronts/')
    profile_photo = models.ImageField(_('Фото сбоку'), upload_to='cars/profiles/')

    driver = models.ForeignKey(
        'telegram_users.TaxiDriver',
        verbose_name=_('Таксист'),
        related_name='cars',
        on_delete=models.CASCADE,
    )

    class Meta:
        verbose_name = _('Автомобиль')
        verbose_name_plural = _('Автомобили')

    def __str__(self):
        return self.name

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__status = self.status

    def save(self, *args, **kwargs):
        if self.status == self.WAITING or self.__status == self.status:
            super().save(*args, **kwargs)
            return

        if self.status == self.APPROVED:
            self.driver.car_id = self.id
            self.driver.save()
            text = (
                'Ваше авто одобрено администрацией!\n\n'
                f'<a href="{settings.PRIVATE_TAXI_ORDERS_CHANNEL_LINK}">Канал с заказами</a>'
            )
        else:
            text = 'К сожалению, ваше авто не прошло верификацию.'

        telegram_service.send_message(
            chat_id=self.driver.telegram_id,
            text=text,
            parse_mode='HTML'
        )
        super().save(*args, **kwargs)


class TaxiDriver(AbstractTelegramUser, TariffMixin):
    """Модель водителя"""
    full_name = models.CharField(_('ФИО'), max_length=150)
    phone_number = models.CharField(_('Номер телефона'), max_length=50, unique=True)
    passport_data = models.CharField(_('Паспортные данные'), max_length=30)
    passport_photo = models.ImageField(_('Фото паспорта'), upload_to='passports/')
    is_active = models.BooleanField(_('Работает'), default=False)
    rating = models.FloatField(
        _('Рейтинг'),
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True,
        blank=True,
        db_index=True,
        default=None
    )
    reviews: list = models.JSONField(default=list)

    car = models.OneToOneField(
        'telegram_users.Car',
        verbose_name=_('Авто'),
        on_delete=models.SET_NULL,
        null=True,
    )

    class Meta:
        verbose_name = _('Таксист')
        verbose_name_plural = _('Таксисты')

    def __str__(self):
        return f'Таксист {self.full_name}'

    def save(self, *args, **kwargs):
        self._update_rating()
        super().save(*args, **kwargs)

    async def asave(self, *args, **kwargs):
        self._update_rating()
        await super().asave(*args, **kwargs)

    def _update_rating(self):
        if not self.reviews:
            return

        self.rating = round(sum(self.reviews) / len(self.reviews), 1)


class TariffDriverRequest(AsyncBaseModel, TariffMixin, RequestStatusMixin):
    """Модель заявки на изменение тарифа водителя"""
    driver = models.ForeignKey(
        'telegram_users.TaxiDriver',
        verbose_name=_('Водитель'),
        on_delete=models.CASCADE,
    )

    class Meta:
        verbose_name = _('Заявка изменения тарифа')
        verbose_name_plural = _('Заявки изменения тарифа')

    def __str__(self):
        return f'Заявка {self.driver.full_name}'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__status = self.status

    def save(self, *args, **kwargs):
        if self.status == self.WAITING or self.__status == self.status:
            super().save(*args, **kwargs)
            return

        if self.status == self.APPROVED:
            text = 'Ваша заявка одобренна администрацией!'
            self.driver.tariff = self.tariff
            self.driver.save()
        else:
            text = 'Ваша заявка не была одобрена администрацией.'


        telegram_service.send_message(
            chat_id=self.driver.telegram_id,
            text=text,
            parse_mode='HTML'
        )
        super().save(*args, **kwargs)