from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from recipes.models import Ingredient, Recipe, Tag
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet

from .filtersets import IngredientSearchFilter, RecipeSearchFilter
from .paginator import SixPagination
from .permissions import IsAuthorOrReadOnly
from .serializers import (FavoriteSerializer, IngredientSerializer,
                          RecipeInListSerializer, RecipeViewSerializer,
                          RecipeWriteSerializer, ShoppingCartSerializer,
                          TagSerializer)


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

    def add_to_list(self, author, recipe, serializer):
        serializer = serializer(
            data={'author': author.id, 'recipe': recipe.id},
            context={'action': 'add'}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(recipe=recipe, author=author)
        response_serializer = RecipeInListSerializer(recipe)
        return Response(
            data=response_serializer.data,
            status=status.HTTP_201_CREATED,
        )

    def remove_from_list(self, author, recipe, serializer):
        serializer = serializer(
            data={'author': author.id, 'recipe': recipe.id},
            context={'action': 'remove'}
        )
        serializer.is_valid(raise_exception=True)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=["POST", "DELETE"],
        permission_classes=[IsAuthenticated]
    )
    def shopping_cart(self, request, pk):
        recipe = get_object_or_404(Recipe, id=pk)
        if request.method == 'POST':
            return self.add_to_list(
                request.user,
                recipe,
                ShoppingCartSerializer
            )
        return self.remove_from_list(
            request.user,
            recipe,
            ShoppingCartSerializer
        )

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
        shopping_list = user.shopping_cart.values(
            'recipe__ingredients__name',
            'recipe__ingredients__measurement_unit',
        ).annotate(
            amount=Sum(
                'recipe__recipe_ingredient_related__amount',
                distinct=True
            )
        )
        count = 1
        text = 'Список покупок:\n'
        for line in shopping_list:
            name, unit, amount = list(line.values())
            text += f'{count}. {name} ({unit}) — {amount}\n'
            count += 1
        return HttpResponse(text, content_type='text/plain')

    @action(
        methods=['POST', 'DELETE'],
        detail=True,
        permission_classes=[IsAuthenticated]
    )
    def favorite(self, request, pk):
        recipe = get_object_or_404(Recipe, id=pk)
        if request.method == 'POST':
            return self.add_to_list(
                request.user,
                recipe,
                FavoriteSerializer
            )
        return self.remove_from_list(
            request.user,
            recipe,
            FavoriteSerializer
        )
