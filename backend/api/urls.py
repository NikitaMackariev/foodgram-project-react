from django.urls import include, path, re_path

from rest_framework.routers import DefaultRouter
from . import views

app_name = 'api'

router = DefaultRouter()

router.register('tags', views.TagViewSet, basename='tags')
router.register('ingredients', views.IngredientViewSet, basename='ingredients')
router.register('recipes', views.RecipeViewSet, basename='recipes')


urlpatterns = [
    path('', include(router.urls)),
    re_path(
        r'recipes/(?P<recipe_id>[0-9]+)/favorite/',
        views.FavoriteView.as_view(),
        name='favorite'
    ),
    re_path(
        r'recipes/(?P<recipe_id>[0-9]+)/shopping_cart/',
        views.ShoppingCartView.as_view(),
        name='shopping_cart'
    ),
    path('users/<int:user_id>/subscribe/', views.SubscribeViewSet.as_view({
        'post': 'create',
        'delete': 'destroy'
    }), name='subscribe'),
]
