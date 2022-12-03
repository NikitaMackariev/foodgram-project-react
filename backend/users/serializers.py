from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from recipes.models import Recipe
from users.models import Follow

User = get_user_model()


class PasswordSerializer(serializers.Serializer):
    """Сериализатор обновления пароля."""
    new_password = serializers.CharField(max_length=150)
    current_password = serializers.CharField(max_length=150)


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор пользователя."""
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'first_name',
            'username',
            'last_name',
            'email',
            'password',
            'id',
            'is_subscribed',
        ]

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request.user.is_anonymous:
            return False
        if Follow.objects.filter(user=request.user, author=obj).exists():
            return True
        return False


class CreateUserSerializer(serializers.ModelSerializer):
    """Сериализатор для создания пользователя"""
    email = serializers.EmailField(
        validators=[UniqueValidator(queryset=User.objects.all())])
    username = serializers.CharField(
        validators=[UniqueValidator(queryset=User.objects.all())])

    class Meta:
        model = User
        fields = (
            'email', 'id', 'password', 'username', 'first_name', 'last_name')
        extra_kwargs = {
            'email': {'required': True},
            'username': {'required': True},
            'password': {'write_only': True},
            'first_name': {'required': True},
            'last_name': {'required': True},
        }

    def create(self, validated_data):
        user = User.objects.create(**validated_data)
        user.set_password(validated_data['password'])
        user.save()
        return user


class UserSubscriptionSerializer(serializers.ModelSerializer):
    """Сериализатор определения подписок."""
    def to_representation(self, instance):
        request = self.context.get('request')
        context = {'request': request}
        return UserSerializer(instance.author, context=context).data


class RecipesMiniSerializers(serializers.ModelSerializer):
    """Сериализатор для получения рецепта в подписке."""

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time',
        )


class UserWithRecipesSerializer(UserSerializer):
    """Сериализатор для получения данных в подписке."""
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
        limit = request.query_params.get('recipes_limit')
        recipes = obj.recipes.only('id', 'name', 'image', 'cooking_time')
        if limit:
            recipes = recipes[:int(limit)]
        return RecipesMiniSerializers(recipes, many=True).data

    def get_recipes_count(self, obj):
        user = obj
        return Recipe.objects.filter(author=user).count()


class SubscriptionSerializer(serializers.ModelSerializer):
    """Сериализатор подписок."""
    class Meta:
        model = Follow
        fields = ('user', 'author')

    def validate(self, data):
        user = data['user']
        author = data['author']
        if user == author:
            raise serializers.ValidationError(
                'Невозможно подписаться на самого себя')
        action = self.context['action']
        user_in_subscription = Follow.objects.filter(
            user=user,
            author=author
        )
        if action == 'subscribe':
            if user_in_subscription:
                raise serializers.ValidationError(
                    'Вы уже подписаны на этого пользователя')
        elif action == 'unsubscribe':
            if not user_in_subscription:
                raise serializers.ValidationError(
                    'Данного пользователя нет в подписках')
            user_in_subscription.delete()
        return data

    def to_representation(self, instance):
        authors = UserWithRecipesSerializer(
            instance.author,
            context={
                'request': self.context.get('request')
            }
        )
        return authors.data
