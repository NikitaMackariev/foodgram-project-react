from django.core.validators import MinValueValidator
from django.db import models

from users.models import User


class Tag(models.Model):
    """Модель тэгов."""

    name = models.CharField(
        verbose_name='Название тега',
        max_length=50,
        unique=True
    )
    color = models.CharField(
        verbose_name='Цветовой HEX-код тега',
        max_length=8,
        unique=True
    )
    slug = models.SlugField(
        unique=True,
        verbose_name='Slug тега'
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """Модель ингредиентов."""

    name = models.CharField(
        verbose_name='Название ингредиента',
        max_length=100
    )
    measurement_unit = models.CharField(
        verbose_name='Единицы измерения ингредиента',
        max_length=50
    )
    amount = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        verbose_name='Количество'
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        unique_together = ('name', 'measurement_unit')

    def __str__(self):
        return self.name


class Recipe(models.Model):
    """Модель рецептов."""

    author = models.ForeignKey(
        User,
        verbose_name='Автор рецепта',
        on_delete=models.CASCADE,
        related_name="recipes"
    )
    name = models.CharField(
        'Название рецепта',
        max_length=200,
        help_text='Введите название рецепта',
    )
    image = models.ImageField(upload_to='')
    text = models.TextField(
        verbose_name='Текст рецепта',
        help_text='Текстовое описание рецепта'
    )
    ingredients = models.ManyToManyField(
        'Ingredient', through='RecipeIngredient',
        verbose_name='Ингридиенты'
    )
    tags = models.ManyToManyField(
        Tag,
        related_name='recipes',
        verbose_name='Теги рецепта'
    )
    cooking_time = models.PositiveIntegerField(
        verbose_name='Время приготовления в минутах',
        help_text='Введите время пригтовления в минутах',
        validators=[
            MinValueValidator(1)]
    )
    pub_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ['-pub_date']


class RecipeIngredient(models.Model):
    """Модель ингредиентов в рецепте."""
    recipe = models.ForeignKey(
        Recipe,
        blank=False,
        null=False,
        on_delete=models.CASCADE,
        related_name='recipe_ingredient_related'
    )
    ingredient = models.ForeignKey(
        'Ingredient',
        blank=False,
        null=False,
        on_delete=models.CASCADE,
        related_name='recipes'
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name='Количество',
    )

    class Meta:
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецепте'
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_recipe_ingredient'
            )
        ]


class ShoppingCart(models.Model):
    """Модель списка покупок."""

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='Покупатель',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='Рецепт для покупки'
    )

    class Meta:
        verbose_name = 'Список покупок'
        ordering = ['author']


class Favorite(models.Model):
    """Модель избранных рецептов."""

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorite',
        verbose_name='Автор'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorite',
        verbose_name='Избранный рецепт'
    )

    class Meta:
        verbose_name = 'Избранный рецепт'
        verbose_name_plural = 'Избранные рецепты'
        ordering = ['author']
