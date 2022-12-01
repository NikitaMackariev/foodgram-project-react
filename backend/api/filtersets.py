from django_filters.rest_framework import FilterSet
from django_filters.rest_framework.filters import (
    AllValuesMultipleFilter,
    BooleanFilter,
    CharFilter,
    ModelChoiceFilter
)
from recipes.models import Ingredient, Recipe
from users.models import User


class IngredientSearchFilter(FilterSet):
    """Фильтрсет ингредиентов."""
    name = CharFilter(lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ('name',)


class RecipeSearchFilter(FilterSet):
    """Фильтрсет рецептов."""
    is_favorited = BooleanFilter(method='filter_is_favorited')
    is_in_shopping_cart = BooleanFilter(method='filter_is_in_shopping_cart')
    tags = AllValuesMultipleFilter(field_name='tags__slug')
    author = ModelChoiceFilter(queryset=User.objects.all())

    def filter_is_favorited(self, queryset, name, value):
        user = self.request.user
        if value and user.is_authenticated:
            return queryset.filter(favorite__author=user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        user = self.request.user
        if value and user.is_authenticated:
            return queryset.filter(shopping_cart__author=user)
        return queryset

    class Meta:
        model = Recipe
        fields = [
            'tags__slug',
            'author',
            'is_favorited',
            'is_in_shopping_cart'
        ]
