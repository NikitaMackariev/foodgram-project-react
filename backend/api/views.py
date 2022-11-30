import sys

from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend


from rest_framework import status, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.views import APIView

from .filtersets import IngredientSearchFilter, RecipeSearchFilter
from .paginator import SixPagination
from .permissions import IsAuthorOrReadOnly
from .serializers import (
    FavoriteSerializer,
    FollowSerializer,
    IngredientSerializer,
    RecipeViewSerializer,
    RecipeWriteSerializer,
    ShoppingCartSerializer,
    TagSerializer,
)
from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag
)
from users.models import User


class SubscribeViewSet(viewsets.ViewSet):
    """API добавления и удаления автора из списка подписок."""
    permission_classes = (permissions.IsAuthenticated,)

    def create(self, request, user_id):
        user = request.user
        data = {
            'user': user.id,
            'author': user_id
        }
        context = {'request': request}
        serializer = FollowSerializer(
            data=data,
            context=context
        )
        if serializer.is_valid():
            serializer.save()
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    def destroy(self, request, user_id):
        follow_author = get_object_or_404(User, pk=user_id)
        data_follow = request.user.follower.filter(author=follow_author)
        if data_follow.exists():
            data_follow.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(data='Вы не подписаны на данного автора.',
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


class RecipeViewSet(viewsets.ModelViewSet):
    """API рецептов"""
    queryset = Recipe.objects.all().order_by('-id')
    permission_classes = (IsAuthorOrReadOnly,)
    pagination_class = SixPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeSearchFilter

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return RecipeViewSerializer
        return RecipeWriteSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def add_to_list(self, request, *args, **kwargs):
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

    def remove_from_list(self, model, user, recipe_id):
        model.objects.get(user=user, recipe_id=recipe_id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=[
            'GET',
        ],
        permission_classes=[IsAuthenticated],
        url_path='download_shopping_cart', url_name='txt_shopping_cart',
    )
    def download_shopping_cart(self, request):
        user = request.user
        if not user.shopping_cart.exists():
            return Response(
                    data='Ваш список покупок пуст.',
                    status=status.HTTP_400_BAD_REQUEST,
                )
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
        try:
            f = open('shopping_cart.txt', 'w')
        except OSError:
            print('Could not open/read file:', 'shopping_cart.txt')
            sys.exit()
        for shopping in shopping_list:
            f.write(shopping)
        f.close()
        return HttpResponse(shopping_list, content_type='text/plain')


class ShoppingCartView(APIView):
    """API списка покупок."""
    permission_classes = (IsAuthenticated,)

    def post(self, request, recipe_id):
        user = self.request.user
        cart_data = {
            'author': user.id,
            'recipe': recipe_id
        }
        cart_context = {'request': request}
        serializer = ShoppingCartSerializer(data=cart_data,
                                            context=cart_context)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, recipe_id):
        user = request.user
        recipe = get_object_or_404(Recipe, id=recipe_id)
        shopping_cart = ShoppingCart.objects.filter(
            author=user,
            recipe=recipe
        )
        if not shopping_cart.exists():
            return Response(
                'Рецепта нет в списке покупок.',
                status=status.HTTP_400_BAD_REQUEST
            )
        shopping_cart.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class FavoriteView(APIView):
    """API избранных рецептов."""
    permission_classes = (IsAuthenticated,)

    def post(self, request, recipe_id):
        user = request.user
        favorite_data = {
            'author': user.id,
            'recipe': recipe_id
        }
        fav_context = {'request': request}
        serializer = FavoriteSerializer(
            data=favorite_data,
            context=fav_context
        )
        if serializer.is_valid():
            serializer.save()
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    def delete(self, request, recipe_id):
        user = request.user
        recipe = get_object_or_404(Recipe, id=recipe_id)
        favorite = Favorite.objects.filter(
            author=user,
            recipe=recipe
        )
        if not favorite.exists():
            return Response(
                'Этот рецепт отсутсвует в избранном.',
                status=status.HTTP_400_BAD_REQUEST
            )
        favorite.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
