from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.urls import reverse
from django.utils.http import urlencode
from recipes.models import Favorite, ShoppingCart

from .models import Follow, User


class FavoriteRecipeInline(admin.TabularInline):
    """Избранные рецепты пользователя."""
    model = Favorite
    extra = 1


class ShoppingCartInline(admin.TabularInline):
    """Список покупок пользователя."""
    model = ShoppingCart
    extra = 1


class UserAdmin(UserAdmin):
    """Админ-панель пользователя."""
    list_display = (
        'username',
        'first_name',
        'last_name',
        'email',
        'favorite',
        'shopping_cart'
    )
    list_filter = ('email', 'username')
    search_fields = ('username',)
    empty_value_display = '-пусто-'
    inlines = (FavoriteRecipeInline, ShoppingCartInline)

    def favorite(self, obj):
        from django.utils.html import format_html
        count = Favorite.objects.filter(author=obj).count()
        url = (
            reverse("admin:recipes_favorite_changelist")
            + "?"
            + urlencode({"user": f"{obj.id}"})
        )
        return format_html(f'<a href="{url}">{count} рецептов</a>')
    favorite.short_description = "В избранном:"

    def shopping_cart(self, obj):
        from django.utils.html import format_html
        count = ShoppingCart.objects.filter(author=obj).count()
        url = (
            reverse("admin:recipes_shoppingcart_changelist")
            + "?"
            + urlencode({"user": f"{obj.id}"})
        )
        return format_html(f'<a href="{url}">{count} рецептов</a>')
    shopping_cart.short_description = "В списке покупок:"


class FollowAdmin(admin.ModelAdmin):
    """Админ-панель подписки."""
    list_display = (
        'user',
        'author'
    )
    list_filter = ('user', 'author')
    search_fields = ('user',)
    empty_value_display = '-пусто-'


admin.site.register(User, UserAdmin)
admin.site.register(Follow, FollowAdmin)
