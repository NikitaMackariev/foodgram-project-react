from rest_framework import serializers

from .utils.base64 import Base64ImageField
from .utils.hex import Hex2NameColor
from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingList,
    Tag,
)
from users.models import User, Follow


class PasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(max_length=150)
    current_password = serializers.CharField(max_length=150)


class UserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "first_name",
            "username",
            "last_name",
            "email",
            "password",
            "id",
            "is_subscribed",
        ]

    def get_is_subscribed(self, obj):
        request = self.context.get("request")
        if request.user.is_anonymous:
            return False
        elif Follow.objects.filter(user=request.user, author=obj).exists():
            return True
        return False


class UserCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "first_name",
            "username",
            "last_name",
            "email",
            "password",
            "id",
        ]

    def create(self, validated_data):
        user = User.objects.create(**validated_data)
        user.set_password(validated_data["password"])
        user.save()
        return user


class TagSerializer(serializers.ModelSerializer):
    color = Hex2NameColor()

    class Meta:
        model = Tag
        fields = ("id", "name", "color", "slug")

    def __str__(self):
        return self.name


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ("id", "name", "measurement_unit")

    def __str__(self):
        return self.name


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    name = serializers.ReadOnlyField(source="ingredient.name")

    class Meta:
        model = RecipeIngredient
        fields = ("id", "name", "amount")


class RecipeViewSerializer(serializers.ModelSerializer):
    ingredients = serializers.SerializerMethodField(read_only=True)
    tags = TagSerializer(read_only=True, many=True)
    author = UserSerializer(read_only=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            "id",
            "name",
            "image",
            "text",
            "ingredients",
            "tags",
            "cooking_time",
            "is_favorited",
            "is_in_shopping_cart",
            "author",
        )

    def __str__(self):
        return self.name

    def get_image(self, obj):
        return obj.image.url

    def get_ingredients(self, obj):
        ingredients = RecipeIngredient.objects.filter(recipe=obj)
        return RecipeIngredientSerializer(ingredients, many=True).data

    def get_is_favorited(self, obj):
        request = self.context.get("request")
        if request.user.is_anonymous:
            return False
        elif Favorite.objects.filter(author=request.user, recipe=obj).exists():
            return True
        else:
            return False

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get("request")
        if request.user.is_anonymous:
            return False
        elif ShoppingList.objects.filter(
            author=request.user, recipe=obj
        ).exists():
            return True
        else:
            return False


class RecipeWriteSerializer(
    serializers.ModelSerializer
):
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
            "name",
            "image",
            "text",
            "ingredients",
            "tags",
            "cooking_time"
        )

    def __str__(self):
        return self.name

    def create(self, validated_data):
        tags = validated_data.pop("tags")
        temp_ingredients = validated_data.pop("ingredients")
        recipe = Recipe.objects.create(
            author=self.context.get("request").user,
            name=validated_data.pop("name"),
            image=validated_data.pop("image"),
            text=validated_data.pop("text"),
            cooking_time=validated_data.pop("cooking_time"),
        )
        recipe.tags.set(tags)
        for ingredient in temp_ingredients:
            ingredient_instance = ingredient["id"]
            amount = ingredient["amount"]
            RecipeIngredient.objects.create(
                recipe=recipe, ingredient=ingredient_instance,  amount=amount
            )
        return recipe

    def update(self, instance, validated_data):
        instance.name = validated_data.get("name", instance.name)
        instance.image = validated_data.get("image", instance.image)
        instance.text = validated_data.get("text", instance.text)
        instance.cooking_time = validated_data.get(
            "cooking_time", instance.cooking_time
        )

        tags = validated_data.get("tags")
        if tags is not None:
            instance.tags.clear()
            for tag in tags:
                instance.tags.add(tag)

        ingredients = validated_data.get("ingredients")
        if ingredients is not None:
            RecipeIngredient.objects.filter(recipe=instance).all().delete()
            for ingredient in ingredients:
                ingredient_id = ingredient["id"]
                amount = ingredient["amount"]
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
        fields = ("id", "name", "image", "cooking_time")


class ShoppingCartCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShoppingList
        fields = ("author", "recipe")

    def to_representation(self, instance):
        return ShortRecipeSerializer(
            instance.recipe, context=self.context
        ).data


class FollowSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "username",
            "first_name",
            "last_name",
            "is_subscribed",
            "recipes",
            "recipes_count",
        )
        extra_kwargs = {
            "email": {"read_only": True},
            "id": {"read_only": True},
            "username": {"read_only": True},
            "first_name": {"read_only": True},
            "last_name": {"read_only": True},
        }

    def get_is_subscribed(self, obj):
        request = self.context.get("request")
        if request.user.is_anonymous:
            return False
        if hasattr(obj, "author"):
            return Follow.objects.filter(
                user=request.user, author=obj.author
            ).exists()
        else:
            return Follow.objects.filter(
                user=request.user, author=obj
            ).exists()

    def get_recipes(self, obj):
        request = self.context.get("request")
        context = {"request": request}
        limit = self.context.get("request").query_params.get("recipes_limit")
        if limit:
            if hasattr(obj, "author"):
                recipes = Recipe.objects.filter(author=obj.author)[
                    : int(limit)
                ]
            else:
                recipes = Recipe.objects.filter(author=obj)[: int(limit)]
        else:
            if hasattr(obj, "author"):
                recipes = Recipe.objects.filter(author=obj.author)
            else:
                recipes = Recipe.objects.filter(author=obj)
        return RecipeViewSerializer(recipes, many=True, context=context).data

    def get_recipes_count(self, obj):
        user = obj
        return Recipe.objects.filter(author=user).count()
