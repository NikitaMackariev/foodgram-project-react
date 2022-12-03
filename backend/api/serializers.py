from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)
from rest_framework import serializers
from users.serializers import UserSerializer

from .utils.base64 import Base64ImageField
from .utils.hex import Hex2NameColor


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор тэгов."""
    color = Hex2NameColor()

    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')

    def __str__(self):
        return self.name


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор ингредиетов."""
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')

    def __str__(self):
        return self.name


class WriteRecipeIngredienSerializer(serializers.ModelSerializer):
    """Сериализатор определения ингредиентов в рецепте."""
    id = serializers.IntegerField()
    amount = serializers.IntegerField()

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class ReadRecipeIngredienSerializer(serializers.ModelSerializer):
    """Сериализатор отображения ингредиентов в рецепте."""
    id = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    measurement_unit = serializers.SerializerMethodField()

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')

    def get_id(self, obj):
        return obj.ingredient.id

    def get_name(self, obj):
        return obj.ingredient.name

    def get_measurement_unit(self, obj):
        return obj.ingredient.measurement_unit


class RecipeViewSerializer(serializers.ModelSerializer):
    """Сериализатор просмотра рецептов."""
    author = UserSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    ingredients = ReadRecipeIngredienSerializer(
        many=True,
        read_only=True,
        source='recipe_ingredient_related'
    )
    is_in_shopping_cart = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = '__all__'

    def __str__(self):
        return self.name

    def get_is_favorited(self, obj):
        user = self.context['request'].user
        if user.is_anonymous:
            return False
        return Favorite.objects.filter(
            author=user,
            recipe=obj
        ).exists()

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if request.user.is_anonymous:
            return False
        if ShoppingCart.objects.filter(
            author=request.user, recipe=obj
        ).exists():
            return True
        return False


class RecipeWriteSerializer(serializers.ModelSerializer):
    """Сериализатор добавления/обновления рецептов."""
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True
    )
    image = Base64ImageField(use_url=True)
    ingredients = WriteRecipeIngredienSerializer(many=True)

    class Meta:
        model = Recipe
        fields = (
            'ingredients', 'tags', 'image',
            'name', 'text', 'cooking_time'
        )

    def create(self, validated_data):
        recipe = Recipe.objects.create(
            author=self.context.get('request').user,
            name=validated_data.pop('name'),
            image=validated_data.pop('image'),
            text=validated_data.pop('text'),
            cooking_time=validated_data.pop('cooking_time'),
        )
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe.tags.set(tags)
        for ingredient in ingredients:
            RecipeIngredient.objects.create(
                ingredient_id=ingredient['id'],
                amount=ingredient['amount'],
                recipe=recipe
            )
        return recipe

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.image = validated_data.get('image', instance.image)
        instance.text = validated_data.get('text', instance.text)
        instance.cooking_time = validated_data.get(
            'cooking_time', instance.cooking_time
        )
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        instance.tags.set(tags)
        RecipeIngredient.objects.filter(recipe=instance).all().delete()
        for ingredient in ingredients:
            amount = ingredient['amount']
            ingredient_id = ingredient['id']
            RecipeIngredient.objects.create(
                ingredient=Ingredient.objects.get(id=ingredient_id),
                amount=amount,
                recipe=instance
            )
        instance.save()
        return instance


class ShoppingCartSerializer(serializers.ModelSerializer):
    """Сериализатор списка покупок."""
    class Meta:
        model = ShoppingCart
        fields = ('author', 'recipe')

    def validate(self, data):
        author = data['author']
        recipe = data['recipe']
        action = self.context['action']
        recipe_in_sh_cart = ShoppingCart.objects.filter(
            recipe=recipe,
            author=author
        )
        if action == 'remove':
            if not recipe_in_sh_cart:
                raise serializers.ValidationError(
                    detail='Данного рецепта нет в списке покупок.')
            recipe_in_sh_cart.delete()
        elif action == 'add':
            if recipe_in_sh_cart:
                raise serializers.ValidationError(
                    detail='Рецепт уже добавлен в список покупок.')
        return data


class RecipeInListSerializer(serializers.ModelSerializer):
    """Сериализатор рецептов в списке."""
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class FavoriteSerializer(RecipeInListSerializer):
    """Сериализатор избранных рецептов."""
    class Meta:
        model = Favorite
        fields = ('author', 'recipe')

    def validate(self, data):
        author = data['author']
        recipe = data['recipe']
        action = self.context['action']
        recipe_in_favorites = Favorite.objects.filter(
            recipe=recipe,
            author=author
        )
        if action == 'remove':
            if not recipe_in_favorites:
                raise serializers.ValidationError(
                    detail='Данного рецепта нет в избранном.')
            recipe_in_favorites.delete()
        elif action == 'add':
            if recipe_in_favorites:
                raise serializers.ValidationError(
                    detail='Рецепт уже добавлен в избранное.')
        return data
