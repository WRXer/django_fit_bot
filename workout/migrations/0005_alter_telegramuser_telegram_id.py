# Generated by Django 5.0 on 2024-01-15 07:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workout', '0004_remove_exercise_date_remove_exercise_set_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='telegramuser',
            name='telegram_id',
            field=models.BigIntegerField(unique=True, verbose_name='ID пользователя в Telegram'),
        ),
    ]