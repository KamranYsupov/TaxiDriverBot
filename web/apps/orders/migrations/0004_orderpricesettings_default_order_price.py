# Generated by Django 4.2.1 on 2025-03-01 06:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0003_alter_orderpricesettings_options_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='orderpricesettings',
            name='default_order_price',
            field=models.PositiveBigIntegerField(default=0, verbose_name='Стоимость подачи'),
        ),
    ]
