from django.contrib import admin

from .models import (
    Order,
    Payment,
    OrderPriceSettings
)
from web.admin import SingletonModelAdmin


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    pass

@admin.register(Payment)
class PaymentUserAdmin(admin.ModelAdmin):
    pass


@admin.register(OrderPriceSettings)
class OrderPriceSettingsAdmin(SingletonModelAdmin):
    pass

