from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from users.models import User

from typing import Any


class UserSerializer(serializers.ModelSerializer[User]):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        field = self.fields['telegram_id']
        field.validators = [
            validator
            for validator in field.validators
            if not isinstance(validator, UniqueValidator)
        ]

    class Meta:
        model = User
        fields = ['id', 'telegram_id', 'first_name', 'last_name', 'accepted_terms']
        read_only_fields = ['accepted_terms']

    def create(self, validated_data: dict[str, Any]) -> User:
        user, created = User.objects.update_or_create(
            telegram_id=validated_data.pop('telegram_id'), defaults=validated_data
        )
        return user
