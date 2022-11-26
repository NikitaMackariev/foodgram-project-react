# Generated by Django 2.2.16 on 2022-11-25 18:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0001_initial'),
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='shopping_recipes',
            field=models.ManyToManyField(related_name='shoppings', to='recipes.Recipe', verbose_name='Рецепты в списке покупок'),
        ),
    ]