from django.db import models
from django.utils.translation import gettext_lazy as _

from .base_manager import AsyncBaseManager
from .models import PriceField


class AsyncBaseModel(models.Model):
    objects = AsyncBaseManager()
    
    class Meta: 
        abstract = True
        
        
class AbstractTelegramUser(AsyncBaseModel):
    telegram_id = models.BigIntegerField(
        verbose_name=_('Телеграм ID'),
        unique=True,
        db_index=True,
    )
    username = models.CharField(
        _('Имя пользователя'),
        max_length=70,
        unique=True,
        db_index=True,
        null=True,
    )

    class Meta: 
        abstract = True


class TimestampMixin(models.Model):
    created_at = models.DateTimeField(
        _('Дата создания'),
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        _('Дата последнего обновления'),
        auto_now=True
    )

    class Meta:
        abstract = True


class SingletonModel(models.Model):
    """Singelton модель"""

    def save(self, *args, **kwargs):
        if self.__class__.objects.count() == 0:
            super().save(*args, **kwargs)
        else:
            existing = self.__class__.objects.get()
            self.id = existing.id
            super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj

    class Meta:
        abstract = True


class TariffMixin(models.Model):
    STANDARD = 'Standard'
    URGENT = 'Urgent'

    TARIFF_CHOICES = [
        (STANDARD, 'Стандартный'),
        (URGENT, 'Срочный'),
    ]

    tariff = models.CharField(
        _('Тариф'),
        choices=TARIFF_CHOICES,
        max_length=20,
        db_index=True,
        default=STANDARD
    )

    class Meta:
        abstract = True


class PriceMixin(models.Model):
    price = PriceField(_('Стоимость'))

    class Meta:
        abstract = True


class RequestStatusMixin(models.Model):
    APPROVED = 'Approved'
    DISAPPROVED = 'Disapproved'
    WAITING = 'Waiting'

    STATUS_CHOICES = [
        (APPROVED, 'Одобрен'),
        (DISAPPROVED, 'Не одобрен'),
        (WAITING, 'Ожидает')
    ]

    status = models.CharField(
        _('Статус'),
        choices=STATUS_CHOICES,
        max_length=20,
        default=WAITING,
    )

    class Meta:
        abstract = True
