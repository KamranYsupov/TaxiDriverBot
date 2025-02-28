from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _
from ulid import ULID

from .base_manager import AsyncBaseManager
        
        
def ulid_default() -> str:
    return str(ULID())
        
        
class AsyncBaseModel(models.Model):
    id = models.CharField( 
        primary_key=True,
        default=ulid_default,
        max_length=26,
        editable=False,
        unique=True,
        db_index=True,
    )
    
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

    rating = models.FloatField(
        _('Рейтинг'),
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True,
        blank=True,
        db_index=True,
        default=None
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
    price = models.PositiveBigIntegerField(_('Стоимость'))

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
