from django.contrib import admin

from .models import (
    Order,
    Payment
)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    pass

@admin.register(Payment)
class PaymentUserAdmin(admin.ModelAdmin):
    pass
