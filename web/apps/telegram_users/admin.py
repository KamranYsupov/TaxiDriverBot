from django.contrib import admin

from .models import (
    TelegramUser,
    TaxiDriver,
    Car,
    TariffDriverRequest
)
from ...admin.mixins import (
    NotAllowedToChangeMixin,
    NotAllowedToAddMixin
)


@admin.register(TelegramUser)
class TelegramUserAdmin(
    NotAllowedToChangeMixin,
    NotAllowedToAddMixin,
    admin.ModelAdmin,
):
    exclude = ('last_add_points_date', )



@admin.register(TaxiDriver)
class TaxiDriverAdmin(admin.ModelAdmin):
    list_filter = ('is_active', 'tariff')

    readonly_fields = ('rating_display', )
    exclude = ('rating', 'reviews',)

    @admin.display(description='Оценка')
    def rating_display(self, obj):
        return f'{obj.rating} ⭐' if obj.rating else 'Нет оценки'

    def get_exclude(self, request, obj=None):
        if not obj:
            return self.exclude + ('car', )

        return self.exclude


@admin.register(Car)
class CarAdmin(NotAllowedToAddMixin, admin.ModelAdmin):
    list_filter = ('status',)

    readonly_fields = (
        'driver',
        'name',
        'gos_number',
        'vin',
        'front_photo',
        'profile_photo',
    )
    search_fields = (
        'name__iregex',
    )

    def has_change_permission(self, request, obj: Car | None = None):
        if not obj or obj.status == Car.WAITING:
            return True

        return False

@admin.register(TariffDriverRequest)
class TariffDriverRequestAdmin(NotAllowedToAddMixin, admin.ModelAdmin):
    list_filter = ('status', 'tariff')

    readonly_fields = ('driver', 'tariff')

    def has_change_permission(self, request, obj: TariffDriverRequest | None = None):
        if not obj or obj.status == TariffDriverRequest.WAITING:
            return True

        return False
