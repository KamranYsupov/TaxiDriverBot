from django.contrib import admin

from .models import (
    TelegramUser,
    TaxiDriver,
    Car,
    TariffDriverRequest
)


@admin.register(TelegramUser)
class TelegramUserAdmin(admin.ModelAdmin):
    fields = (
        'telegram_id',
        'username',
        'rating_display',
        'tariff',
    )
   # exclude = ('reviews', )

    def has_change_permission(self, request, obj=None):
        return False

    @admin.display(description='Оценка')
    def rating_display(self, obj):
        return f'{obj.rating} ⭐'


@admin.register(TaxiDriver)
class TaxiDriverAdmin(admin.ModelAdmin):
    fields = ('rating_display', 'reviews')
    readonly_fields = ('rating_display', )

    @admin.display(description='Оценка')
    def rating_display(self, obj):
        return f'{obj.rating} ⭐'


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