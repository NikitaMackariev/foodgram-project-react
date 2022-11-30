from api.paginator import SixPagination
from api.permissions import UserPermission
from api.serializers import UserWithRecipesSerializer
from django.contrib.auth.hashers import check_password
from django.shortcuts import get_object_or_404
from djoser.views import TokenCreateView, UserViewSet
from rest_framework import permissions, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.status import HTTP_400_BAD_REQUEST

from .models import Follow, User
from .serializers import (
    UserSerializer,
    PasswordSerializer)

USER_BLOCKED = 'Аккаунт не активен!'


class UserViewSet(UserViewSet):
    """API пользователя."""
    queryset = User.objects.all().prefetch_related('recipes')
    serializer_class = UserSerializer
    pagination_class = SixPagination
    permission_classes = (UserPermission,)

    @action(
        detail=False,
        methods=['GET'],
        permission_classes=(permissions.IsAuthenticated,)
    )
    def me(self, request):
        serializer = UserSerializer(request.user, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        detail=False,
        methods=['POST'],
        permission_classes=(permissions.IsAuthenticated,)
    )
    def set_password(self, request):
        serializer = PasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        password = serializer.validated_data['current_password']
        new_password = serializer.validated_data['new_password']
        username = request.user.username
        user = get_object_or_404(
            self.get_queryset(),
            username=username
        )
        if check_password(password, user.password):
            user.set_password(new_password)
            user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=False,
        methods=['GET'],
        url_path='subscriptions',
        permission_classes=(permissions.IsAuthenticated,),
    )
    def subscriptions(self, request):
        queryset = User.objects.filter(
            id__in=Follow.objects.filter(user=request.user).values_list(
                'author_id', flat=True
            )
        )
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = UserWithRecipesSerializer(
                page,
                many=True,
                context={
                    'request': request,
                },
            )
            return self.get_paginated_response(serializer.data)
        serializer = UserWithRecipesSerializer(
            queryset,
            many=True,
            context={
                'request': request,
            },
        )
        return Response(serializer.data)


class TokenCreateNonBlockedUserView(TokenCreateView):
    permission_classes = (AllowAny, )

    def _action(self, serializer):
        if serializer.user.is_not_active:
            return Response(
                {'errors': USER_BLOCKED},
                status=HTTP_400_BAD_REQUEST,
            )
        return super()._action(serializer)
