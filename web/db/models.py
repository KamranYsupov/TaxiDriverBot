from django.core.validators import MinValueValidator
from django.db import models


class PriceField(models.FloatField):
    """Поле цены"""
    default_validators = [MinValueValidator(0.0)]