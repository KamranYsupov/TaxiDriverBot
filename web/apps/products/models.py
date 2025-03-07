from django.db import models
from django.utils.translation import gettext_lazy as _
from web.db.model_mixins import (
    AsyncBaseModel,
    TimestampMixin,
    PriceMixin
)


class Product(AsyncBaseModel, PriceMixin, TimestampMixin):
    """Модель товара"""

    name = models.CharField(_('Название'), max_length=150)
    description = models.TextField(_('Описание'), max_length=4000)

    class Meta:
        verbose_name = _('Товар')
        verbose_name_plural = _('Товары')

    def __str__(self):
        return self.name


