# Generated by Django 4.2.1 on 2025-03-07 06:02

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0003_alter_product_description'),
        ('orders', '0014_alter_order_from_latitude_alter_payment_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='payment',
            name='product',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='payments', to='products.product', verbose_name='Товар'),
        ),
    ]
