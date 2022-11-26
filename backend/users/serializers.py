from rest_framework import serializers

from users.models import User, Follow


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
        elif Follow.objects.filter(user=request.user, author=obj).exists():
            return True
        return False


class UserCreateSerializer(serializers.ModelSerializer):
    """Сериализатор создания пользователя."""
    class Meta:
        model = User
        fields = [
            'first_name',
            'username',
            'last_name',
            'email',
            'password',
            'id',
        ]

    def create(self, validated_data):
        user = User.objects.create(**validated_data)
        user.set_password(validated_data['password'])
        user.save()
        return user


class GetTokenSerializer(serializers.Serializer):
    """
    Сериализатор для обработки запросов на получение токена.
    """
    email = serializers.EmailField(max_length=254)
    password = serializers.CharField(max_length=128)

    def validate(self, data):
        try:
            user = User.objects.get(email=data['email'])
        except User.DoesNotExist:
            raise serializers.ValidationError(
                'Предоставлен email незарегистрированного пользователя.'
            )
        if user.check_password(data['password']):
            return data
        raise serializers.ValidationError(
            'Неверный пароль для пользователя с указанным email.'
        )
