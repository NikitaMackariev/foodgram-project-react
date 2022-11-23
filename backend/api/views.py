from django.contrib.auth.hashers import check_password
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError
from django.db import transaction, IntegrityError
from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend


from rest_framework import status, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from .filtersets import IngredientSearchFilter, RecipeSearchFilter
from .mixins import CustomUserViewSet
from .paginator import SixPagination
from .permissions import IsAuthorOrReadOnly, UserPermission
from .serializers import (
    FollowSerializer,
    IngredientSerializer,
    PasswordSerializer,
    RecipeViewSerializer,
    RecipeWriteSerializer,
    ShortRecipeSerializer,
    TagSerializer,
    UserSerializer
)
from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag
)
from users.models import Follow, User


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
            serializer = FollowSerializer(
                page,
                many=True,
                context={
                    'request': request,
                },
            )
            return self.get_paginated_response(serializer.data)
        serializer = FollowSerializer(
            queryset,
            many=True,
            context={
                'request': request,
            },
        )
        return Response(serializer.data)


class FollowViewSet(viewsets.ViewSet):
    """API подписки."""
    permission_classes = (permissions.IsAuthenticated,)

    def create(self, request, user_id):
        follow_author = get_object_or_404(User, pk=user_id)
        serializer = FollowSerializer(data=request.data)
        if follow_author == self.request.user:
            return Response(
                data='Вы пытаетесь подписаться на себя',
                status=status.HTTP_400_BAD_REQUEST,
            )
        if Follow.objects.filter(user=self.request.user,
                                 author=follow_author).exists():
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data='Вы уже подписаны на пользователя'
            )
        if serializer.is_valid():
            Follow.objects.create(
                user=request.user,
                author=follow_author
            )
            serializer = FollowSerializer(
                follow_author, context={'request': request}
            )
            return Response(serializer.data, status.HTTP_201_CREATED)
        return Response(status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, user_id):
        follow_author = get_object_or_404(User, pk=user_id)
        data_follow = request.user.follower.filter(author=follow_author)
        if data_follow.exists():
            data_follow.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(data='Вы не подписаны на автора',
                            status=status.HTTP_400_BAD_REQUEST)


class TagViewSet(ReadOnlyModelViewSet):
    """API тэгов."""
    queryset = Tag.objects.all()
    pagination_class = None
    serializer_class = TagSerializer


class IngredientViewSet(ReadOnlyModelViewSet):
    """API ингредиентов."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientSearchFilter


class RecipeViewSet(ModelViewSet):
    """API рецептов."""

    queryset = Recipe.objects.all()
    permission_classes = [IsAuthorOrReadOnly]
    pagination_class = SixPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeSearchFilter

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return RecipeViewSerializer
        return RecipeWriteSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(
                page, many=True, context={'request': request}
            )
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(
            queryset, many=True, context={'request': request}
        )
        return Response(serializer.data)

    @transaction.atomic
    def create_instance(self, author, recipe_id, model):
        try:
            obj, created = model.objects.get_or_create(
                author=author,
                recipe_id=recipe_id
            )
        except IntegrityError:
            print('Integrity error occurs while handling transaction')
        if not created:
            raise ValidationError(f'{model.__class__.__name__} already exists')
        serializer_obj = Recipe.objects.get(pk=recipe_id)
        serializer = ShortRecipeSerializer(instance=serializer_obj)
        return Response(
            data=serializer.data,
            status=status.HTTP_201_CREATED,
        )

    def delete_instance(self, author, recipe_id, model):
        model.objects.get(author=author, recipe_id=recipe_id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['POST', 'DELETE'],
        permission_classes=[IsAuthenticated]
    )
    def shopping_cart(self, request, pk):
        if request.method == 'POST':
            try:
                ShoppingCart.objects.get(recipe_id=pk, author=request.user)
                return Response(
                    data='Рецепт уже добавлен в список покупок',
                    status=status.HTTP_400_BAD_REQUEST,
                )
            except Exception:
                return self.create_instance(
                    author=request.user, recipe_id=pk, model=ShoppingCart
                )
        try:
            return self.delete_instance(request.user, pk, ShoppingCart)
        except Exception:
            return Response(
                data='Рецепта в списке покупок нет',
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(
        detail=False,
        methods=[
            'GET',
        ],
        permission_classes=[IsAuthenticated],
    )
    def download_shopping_cart(self, request):
        instances = ShoppingCart.objects.filter(author=request.user)
        shopping_list = []
        for instance in instances:
            recipe = Recipe.objects.get(name=instance.recipe)
            recipe_ingredients = RecipeIngredient.objects.filter(recipe=recipe)
            for ingredient in recipe_ingredients:
                shopping_list.append(
                    f'{ingredient.recipe}: {ingredient.ingredient.name}'
                    f' - {ingredient.amount}\n'
                )
        f = open('shopping_cart.txt', 'w')
        for shopping in shopping_list:
            f.write(shopping)
        f.close()
        return HttpResponse(shopping_list, content_type='text/plain')

    @action(
        detail=True,
        methods=['POST', 'DELETE'],
        permission_classes=[IsAuthenticated]
    )
    def favorite(self, request, pk):
        if request.method == 'POST':
            try:
                Favorite.objects.get(recipe_id=pk, author=request.user)
                return Response(
                    data='Рецепт уже добавлен в избранное',
                    status=status.HTTP_400_BAD_REQUEST,
                )
            except Exception:
                return self.create_instance(
                    author=request.user, recipe_id=pk, model=Favorite
                )
        try:
            return self.delete_instance(request.user, pk, Favorite)
        except Exception:
            return Response(
                data='Рецепта в избранном нет',
                status=status.HTTP_400_BAD_REQUEST
            )
