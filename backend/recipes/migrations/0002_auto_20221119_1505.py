# Generated by Django 2.2.16 on 2022-11-19 15:05

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='recipeingredient',
            name='amount',
            field=models.DecimalField(decimal_places=1, max_digits=30, validators=[django.core.validators.MaxValueValidator(10), django.core.validators.MinValueValidator(0.1)], verbose_name='Количество'),
        ),
    ]