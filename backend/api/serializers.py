from rest_framework import serializers
from rest_framework.exceptions import ValidationError
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


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Сериализатор ингредиентов в рецепте."""
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    name = serializers.ReadOnlyField(source='ingredient.name')

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'amount')


class RecipeViewSerializer(serializers.ModelSerializer):
    """Сериализатор рецептов."""
    ingredients = serializers.SerializerMethodField(read_only=True)
    tags = TagSerializer(read_only=True, many=True)
    author = UserSerializer(read_only=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'text',
            'ingredients',
            'tags',
            'cooking_time',
            'is_favorited',
            'is_in_shopping_cart',
            'author',
        )

    def __str__(self):
        return self.name

    def get_image(self, obj):
        return obj.image.url

    def get_ingredients(self, obj):
        ingredients = RecipeIngredient.objects.filter(recipe=obj)
        return RecipeIngredientSerializer(ingredients, many=True).data

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
        elif ShoppingCart.objects.filter(
            author=request.user, recipe=obj
        ).exists():
            return True
        else:
            return False


class RecipeWriteSerializer(
    serializers.ModelSerializer
):
    """Сериализатор добавления/обновления рецептов."""
    ingredients = RecipeIngredientSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all()
    )
    image = Base64ImageField(
        max_length=None,
        use_url=True,
    )

    class Meta:
        model = Recipe
        fields = (
            'name',
            'image',
            'text',
            'ingredients',
            'tags',
            'cooking_time'
        )

    def __str__(self):
        return self.name

    def validate_cooking_time(self, value):
        if value < 0:
            raise ValidationError('Значение не может быть меньше нуля.')
        return value

    def validate_ingredients(self, ingredients):
        len_ingredients = len(ingredients)
        len_unique_ingredients = len(
            set([ingredient.get('ingredient') for ingredient in ingredients])
        )
        if len_ingredients != len_unique_ingredients:
            raise ValidationError('Ингредиенты не должны повторяться.')
        return ingredients

    def validate_tags(self, tags):
        if len(tags) != len(set(tags)):
            raise ValidationError('Теги должны быть уникальны.')
        return tags

    def create(self, validated_data):
        tags = validated_data.pop('tags')
        temp_ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(
            author=self.context.get('request').user,
            name=validated_data.pop('name'),
            image=validated_data.pop('image'),
            text=validated_data.pop('text'),
            cooking_time=validated_data.pop('cooking_time'),
        )
        recipe.tags.set(tags)
        for ingredient in temp_ingredients:
            ingredient_instance = ingredient['id']
            amount = ingredient['amount']
            RecipeIngredient.objects.create(
                recipe=recipe, ingredient=ingredient_instance,  amount=amount
            )
        return recipe

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.image = validated_data.get('image', instance.image)
        instance.text = validated_data.get('text', instance.text)
        instance.cooking_time = validated_data.get(
            'cooking_time', instance.cooking_time
        )

        tags = validated_data.get('tags')
        if tags is not None:
            instance.tags.clear()
            for tag in tags:
                instance.tags.add(tag)

        ingredients = validated_data.get('ingredients')
        if ingredients is not None:
            RecipeIngredient.objects.filter(recipe=instance).all().delete()
            for ingredient in ingredients:
                ingredient_id = ingredient['id']
                amount = ingredient['amount']
                RecipeIngredient.objects.create(
                    recipe=instance, ingredient=ingredient_id, amount=amount
                )
            instance.save()
        return instance

    def to_representation(self, instance):
        return RecipeViewSerializer(instance, context=self.context).data


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
                user=request.user, author=obj.author
            ).exists()
        else:
            return Follow.objects.filter(
                user=request.user, author=obj
            ).exists()

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
