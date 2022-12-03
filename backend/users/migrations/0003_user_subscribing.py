# Generated by Django 3.2.8 on 2022-12-03 12:59

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_alter_user_is_active'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='subscribing',
            field=models.ManyToManyField(through='users.Follow', to=settings.AUTH_USER_MODEL, verbose_name='Подписчики'),
        ),
    ]
