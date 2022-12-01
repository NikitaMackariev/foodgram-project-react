from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from .utils.base64 import Base64ImageField
from .utils.hex import Hex2NameColor
from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag,
)
from users.models import User, Follow
from users.serializers import UserSerializer


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
    """Сериализатор определения ингредиентов в рецепте"""

    id = serializers.IntegerField()
    amount = serializers.IntegerField()

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class ReadRecipeIngredienSerializer(serializers.ModelSerializer):
    """Сериализатор отображения ингредиентов в рецепте"""

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
    author = UserSerializer()
    tags = TagSerializer(many=True, read_only=True)
    ingredients = ReadRecipeIngredienSerializer(
        many=True,
        read_only=True,
        source='recipe_ingredient_related'
    )
    is_in_shopping_cart = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()

    def get_user(self):
        user = None
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            user = request.user
        return user

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

    class Meta:
        model = Recipe
        fields = '__all__'


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


class ShortRecipeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class ShoppingCartSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShoppingCart
        fields = ('author', 'recipe')
        validators = (
            UniqueTogetherValidator(
                queryset=ShoppingCart.objects.all(),
                fields=('author', 'recipe'),
                message='Рецепт уже в находиться в корзине.'
            ),
        )

    def to_representation(self, instance):
        return ShortRecipeSerializer(
            instance.recipe, context=self.context
        ).data


class UserWithRecipesSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count',
        )
        extra_kwargs = {
            'email': {'read_only': True},
            'id': {'read_only': True},
            'username': {'read_only': True},
            'first_name': {'read_only': True},
            'last_name': {'read_only': True},
        }
        validators = (
            UniqueTogetherValidator(
                queryset=Follow.objects.all(),
                fields=('user', 'author'),
                message='Данный автор уже находиться в избранном.'
            ),
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request.user.is_anonymous:
            return False
        if hasattr(obj, 'author'):
            return Follow.objects.filter(
                user=request.user, author=obj.author).exists()
        return Follow.objects.filter(
            user=request.user, author=obj).exists()

    def get_recipes(self, obj):
        request = self.context.get('request')
        context = {'request': request}
        limit = self.context.get('request').query_params.get('recipes_limit')
        if limit:
            if hasattr(obj, 'author'):
                recipes = Recipe.objects.filter(author=obj.author)[
                    : int(limit)
                ]
            else:
                recipes = Recipe.objects.filter(author=obj)[: int(limit)]
        else:
            if hasattr(obj, 'author'):
                recipes = Recipe.objects.filter(author=obj.author)
            else:
                recipes = Recipe.objects.filter(author=obj)
        return RecipeViewSerializer(recipes, many=True, context=context).data

    def get_recipes_count(self, obj):
        user = obj
        return Recipe.objects.filter(author=user).count()


class FollowSerializer(serializers.ModelSerializer):
    """Сериализатор подписки."""
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    author = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all()
    )

    class Meta:
        model = Follow
        fields = ('user', 'author')
        validators = (
            UniqueTogetherValidator(
                queryset=Follow.objects.all(),
                fields=('user', 'author'),
                message='Вы уже подписаны на данного пользователя.'
            ),
        )

    def validate(self, data):
        user = self.context['request'].user
        author = data.get('author')
        if user == author:
            raise serializers.ValidationError(
                'Невозможно подписаться на себя.'
            )
        return data

    def to_representation(self, instance):
        authors = UserWithRecipesSerializer(
            instance.author,
            context={
                'request': self.context.get('request')
            }
        )
        return authors.data


class FavoriteSerializer(serializers.ModelSerializer):
    """Сериализатор избранных рецептов."""
    class Meta:
        model = Favorite
        fields = ('author', 'recipe')
        validators = (
            UniqueTogetherValidator(
                queryset=Favorite.objects.all(),
                fields=('author', 'recipe'),
                message='Рецепт уже в находиться в избранном.'
            ),
        )

    def to_representation(self, instance):
        recipes = ShortRecipeSerializer(
            instance.recipe,
            context={
                'request': self.context.get('request')
            }
        )
        return recipes.data
