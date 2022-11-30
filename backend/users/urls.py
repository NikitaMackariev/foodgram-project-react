from django.urls import include, path

from djoser.views import TokenDestroyView

from rest_framework.routers import DefaultRouter

from users.views import (UserViewSet,
                         TokenCreateNonBlockedUserView)

app_name = 'users'

router = DefaultRouter()
router.register('users', UserViewSet, basename='users')

urlpatterns = [
    path('', include(router.urls)),
    path(
        'auth/token/login/',
        TokenCreateNonBlockedUserView.as_view(), name='login'
    ),
    path('auth/token/logout/', TokenDestroyView.as_view(), name='logout'),
    path('', include('djoser.urls')),
]
