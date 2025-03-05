from django.contrib import admin

from .models import (
    Order,
    Payment,
    OrderPriceSettings
)
from web.admin.mixins import (
    SingletonModelAdmin,
    NotAllowedToAddMixin,
    NotAllowedToChangeMixin
)


@admin.register(Order)
class OrderAdmin(
    NotAllowedToAddMixin,
    NotAllowedToChangeMixin,
    admin.ModelAdmin
):
    fieldsets = (
        ('Основная информация', {
            'fields': (
                'type',
                'telegram_user',
                'driver'
            )
        }),
        ('Информация о поездке', {
            'fields': (
                'from_address',
                'to_address'
            )
        }),
        ('Детали поездки', {
            'fields': (
                'travel_length_km',
                'travel_time_minutes',
                'price',
            )
        }),
    )

    list_display_links = ('from_address', 'to_address',)
    list_display = list_display_links + ('price', )

    list_filter = ('type', )


@admin.register(Payment)
class PaymentAdmin(
    NotAllowedToAddMixin,
    NotAllowedToChangeMixin,
    admin.ModelAdmin
):
    list_display = (
        'yookassa_payment_id',
        'price',
        'telegram_user',
    )

    list_filter = ('type',)

    fields = (
        'yookassa_payment_id',
        'type',
        'status',
        'price',
    )
    search_fields = ('yookassa_payment_id', )

    def get_fields(self, request, obj=None):
        if obj.order_id and 'order' not in self.fields:
            self.fields += ('order', )
        if obj.product_id and 'product' not in self.fields:
            self.fields += ('product', )

        return self.fields


@admin.register(OrderPriceSettings)
class OrderPriceSettingsAdmin(SingletonModelAdmin):
    pass

