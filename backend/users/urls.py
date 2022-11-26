from django.urls import include, path

from rest_framework.routers import DefaultRouter

from users.views import (GetTokenView, DelTokenView,
                         UserViewSet)

app_name = 'users'

router = DefaultRouter()
router.register('users', UserViewSet, basename='users')

urlpatterns = [
    path('', include(router.urls)),
    path(
        'auth/token/login/',
        GetTokenView.as_view(),
        name='token_login'
    ),
    path(
        'auth/token/logout/',
        DelTokenView.as_view(),
        name='token_logout'
    ),
]
