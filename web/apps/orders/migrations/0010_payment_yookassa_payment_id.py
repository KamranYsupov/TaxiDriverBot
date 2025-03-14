# Generated by Django 4.2.1 on 2025-03-04 05:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0009_payment_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='payment',
            name='yookassa_payment_id',
            field=models.CharField(db_index=True, editable=False, max_length=40, unique=True, verbose_name='Yookassa payment ID'),
            preserve_default=False,
        ),
    ]
