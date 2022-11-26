from django.contrib.auth.hashers import check_password
from django.shortcuts import get_object_or_404


from rest_framework import status, permissions
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response

from api.paginator import SixPagination
from api.permissions import UserPermission
from api.serializers import UserWithRecipesSerializer
from .serializers import (
    GetTokenSerializer,
    PasswordSerializer,
    UserSerializer
)

from .models import Follow, User
from .mixins import CustomUserViewSet


class UserViewSet(CustomUserViewSet):
    """API пользователя."""
    queryset = User.objects.all()
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


class GetTokenView(ObtainAuthToken):
    """API получения токена."""
    name = 'Получение токена'
    description = 'Получение токена'
    permission_classes = (AllowAny,)

    def post(self, request):
        serializer = GetTokenSerializer(data=request.data)
        if serializer.is_valid():
            user = get_object_or_404(
                User, email=serializer.validated_data['email']
            )
            token, created = Token.objects.get_or_create(user=user)
            return Response(
                {
                    'auth_token': token.key
                },
                status=status.HTTP_201_CREATED
            )
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


class DelTokenView(APIView):
    name = 'Удаление токена'
    description = 'Удаление токена'
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        token = request.auth
        token.delete()
        return Response(
            status=status.HTTP_204_NO_CONTENT
        )