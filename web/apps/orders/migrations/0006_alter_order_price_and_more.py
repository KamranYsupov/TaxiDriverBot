# Generated by Django 4.2.1 on 2025-03-01 07:28

from django.db import migrations
import web.db.models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0005_order_travel_length_km_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='price',
            field=web.db.models.PriceField(verbose_name='Стоимость'),
        ),
        migrations.AlterField(
            model_name='orderpricesettings',
            name='default_order_price',
            field=web.db.models.PriceField(default=0, verbose_name='Стоимость подачи'),
        ),
        migrations.AlterField(
            model_name='orderpricesettings',
            name='price_for_km',
            field=web.db.models.PriceField(default=0, verbose_name='Стоимость за километр'),
        ),
        migrations.AlterField(
            model_name='orderpricesettings',
            name='price_for_travel_minute',
            field=web.db.models.PriceField(default=0, verbose_name='Стоимость за минуту пути'),
        ),
        migrations.AlterField(
            model_name='payment',
            name='price',
            field=web.db.models.PriceField(verbose_name='Стоимость'),
        ),
    ]
