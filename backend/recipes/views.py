from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile
from django.http import FileResponse

from rest_framework import status
from rest_framework.response import Response

from .models import Recipe, RecipeIngredient, ShoppingCart


@login_required
def shopping_list(request, pk):
    if request.user.is_staff:
        samples = ShoppingCart.objects.filter(author_id=pk)
        shopping_list = []
        for sample in samples:
            recipe = Recipe.objects.get(name=sample.recipe)
            recipe_ingredients = RecipeIngredient.objects.filter(recipe=recipe)
            for ingredient in recipe_ingredients:
                shopping_list.append(
                    f'{ingredient.recipe}: {ingredient.ingredient.name}'
                    f' - {ingredient.amount}'
                )
        print(shopping_list)
        file = ContentFile('/n'.join(shopping_list))
        response = FileResponse(file.read(), content_type='text/plain')
        response[
            'Content-Disposition'
        ] = 'attachment; filename=shopping_list.txt'
        return response
    return Response(status=status.HTTP_400_BAD_REQUEST)
