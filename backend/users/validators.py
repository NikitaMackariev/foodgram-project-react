from rest_framework.exceptions import ValidationError


def validate_username(username):
    """Проверка имени пользователя."""
    if len(username) == 2:
        raise ValidationError('Недопустимое имя пользователя!')
