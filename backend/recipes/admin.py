from django.contrib import admin

from .models import (Favorite, Ingredient, Recipe,
                     RecipeIngredient, ShoppingCart, Tag)


class IngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1


class IngredientAdmin(admin.ModelAdmin):
    """Админ-панель ингредиентов."""
    list_display = ('name', 'measurement_unit')
    list_filter = ('name',)
    search_fields = ('name',)
    empty_value_display = '-пусто-'


class RecipeAdmin(admin.ModelAdmin):
    """Админ-панель рецептов."""
    inlines = (IngredientInline,)
    list_display = ('author', 'name', 'favorites')
    search_fields = ('author',)
    list_filter = ('author', 'name', 'tags')
    empty_value_display = '-пусто-'

    def favorites(self, obj):
        favorite = Favorite.objects.filter(recipe=obj)
        return favorite.count()


class RecipeIngredientAdmin(admin.ModelAdmin):
    """Админ-панель ингредиентов в рецепте."""
    list_display = ('id', 'recipe', 'ingredient', 'amount')
    empty_value_display = '-пусто-'


class TagAdmin(admin.ModelAdmin):
    """Админ-панель тэгов."""
    list_display = ('slug', 'name', 'color')
    list_filter = ('name', 'color', 'slug')
    search_fields = ('name',)
    empty_value_display = '-пусто-'


class FavoriteAdmin(admin.ModelAdmin):
    """Админ-панель избранных рецептов."""
    list_display = ('author', 'recipe')
    empty_value_display = '-пусто-'


class ShoppingCartAdmin(admin.ModelAdmin):
    """Админ-панель избранных рецептов."""
    list_display = (
        'author',
        'recipe'
    )
    list_filter = ('author', 'recipe')
    search_fields = ('author',)
    empty_value_display = '-пусто-'


admin.site.register(Favorite, FavoriteAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(RecipeIngredient, RecipeIngredientAdmin)
admin.site.register(ShoppingCart, ShoppingCartAdmin)
admin.site.register(Tag, TagAdmin)
