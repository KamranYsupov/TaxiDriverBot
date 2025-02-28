from django.contrib import admin

from .models import (
    TelegramUser,
    TaxiDriver,
    Car,
    TariffDriverRequest
)


@admin.register(TelegramUser)
class TelegramUserAdmin(admin.ModelAdmin):
    pass


@admin.register(TaxiDriver)
class TaxiDriverAdmin(admin.ModelAdmin):
    pass


@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
    readonly_fields = (
        'driver',
        'name',
        'gos_number',
        'vin',
        'photo',
    )

    def has_change_permission(self, request, obj: Car | None = None):
        if not obj:
            return True

        if obj.status != Car.WAITING:
            return False

        return True


@admin.register(TariffDriverRequest)
class TariffDriverRequestAdmin(admin.ModelAdmin):
    readonly_fields = ('driver', 'tariff')

    def has_change_permission(self, request, obj: TariffDriverRequest | None = None):
        if not obj:
            return True

        if obj.status != TariffDriverRequest.WAITING:
            return False

        return True