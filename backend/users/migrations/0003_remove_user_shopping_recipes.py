# Generated by Django 2.2.16 on 2022-11-25 19:19

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_user_shopping_recipes'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='shopping_recipes',
        ),
    ]