from rest_framework import serializers

from .models import User, Follow


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
