# Generated by Django 4.2.1 on 2025-03-02 08:57

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0007_alter_payment_type'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='order',
            name='current_active_drivers_count',
        ),
        migrations.RemoveField(
            model_name='order',
            name='miss_drivers_count',
        ),
    ]
