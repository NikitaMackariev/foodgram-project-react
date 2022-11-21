from django.urls import include, path

from rest_framework.routers import DefaultRouter
from djoser.views import TokenCreateView, TokenDestroyView
from . import views

app_name = 'api'

router = DefaultRouter()
router.register('users', views.UserViewSet, basename='users')
router.register('tags', views.TagViewSet, basename='tags')
router.register('ingredients', views.IngredientViewSet, basename='ingredients')
router.register('recipes', views.RecipeViewSet, basename='recipes')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/token/login/', TokenCreateView.as_view(), name='token_login'),
    path('auth/token/logout/',
         TokenDestroyView.as_view(), name='token_logout'),
    path('users/<int:user_id>/subscribe/', views.FollowViewSet.as_view({
        'post': 'create',
        'delete': 'destroy'
    }), name='subscribe'),
]
