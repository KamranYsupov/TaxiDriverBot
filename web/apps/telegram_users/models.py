from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from web.db.model_mixins import (
    AsyncBaseModel,
    AbstractTelegramUser,
    TariffMixin
)
from web.services.telegram_service import telegram_service


class TelegramUser(AbstractTelegramUser, TariffMixin):
    """Модель telegram пользователя(заказчика)"""

    class Meta:
        verbose_name = _('пользователь')
        verbose_name_plural = _('Telegram пользователи')

    def __str__(self):
        return self.username if self.username else f'Пользователь {self.id}'


class Car(AsyncBaseModel):
    """Модель авто"""

    APPROVED = 'Approved'
    DISAPPROVED = 'Disapproved'
    WAITING = 'Waiting'

    STATUS_CHOICES = [
        (APPROVED, _('Одобрен')),
        (DISAPPROVED, _('Не одобрен')),
        (WAITING, _('Ожидает'))
    ]

    name = models.CharField(_('Название'), max_length=150)
    gos_number = models.CharField(_('Государственный номер'), max_length=20)
    vin = models.CharField(_('ВИН'), max_length=20)
    photo = models.ImageField(_('Фото'), upload_to='cars/')
    status = models.CharField(
        _('Статус'),
        choices=STATUS_CHOICES,
        max_length=20,
        default=WAITING,
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
            text = (
                'Ваше авто одобрено администрацией!\n\n'
                f'<a href="{settings.PRIVATE_ORDERS_CHANNEL_LINK}">Канал с заказами</a>'
            )
        else:
            text = 'К сожалению, ваше авто не прошло верификацию.'

        response = telegram_service.send_message(
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
    child_chair = models.BooleanField(_('Детское кресло'), default=False)
    in_work = models.BooleanField(_('Работает'), default=False)

    car = models.OneToOneField(
        'telegram_users.Car',
        verbose_name=_('Авто'),
        on_delete=models.SET_NULL,
        related_name='driver',
        null=True,
    )

    class Meta:
        verbose_name = _('Таксист')
        verbose_name_plural = _('Таксисты')

    def __str__(self):
        return f'Таксист {self.full_name}'