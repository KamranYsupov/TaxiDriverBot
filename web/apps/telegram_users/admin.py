from django.contrib import admin

from .models import (
    TelegramUser,
    TaxiDriver,
    Car
)


@admin.register(TelegramUser)
class TelegramUserAdmin(admin.ModelAdmin):
    pass


@admin.register(TaxiDriver)
class TaxiDriverAdmin(admin.ModelAdmin):
    pass


@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
    pass