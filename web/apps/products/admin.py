from django.contrib import admin

from web.apps.products.models import Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    pass