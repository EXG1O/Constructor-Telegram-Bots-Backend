from rest_framework import serializers

from drf_spectacular.utils import extend_schema_serializer

from ..models import User

from typing import Any


@extend_schema_serializer(component_name='TelegramBotUserSerializer')
class UserSerializer(serializers.ModelSerializer[User]):
    class Meta:
        model = User
        fields = [
            'id',
            'telegram_id',
            'username',
            'first_name',
            'last_name',
            'is_bot',
            'is_premium',
            'is_allowed',
            'is_blocked',
            'activated_date',
        ]
        read_only_fields = [
            'telegram_id',
            'username',
            'first_name',
            'last_name',
            'is_bot',
            'is_premium',
            'activated_date',
        ]

    def update(self, user: User, validated_data: dict[str, Any]) -> User:
        user.is_allowed = validated_data.get('is_allowed', user.is_allowed)
        user.is_blocked = validated_data.get('is_blocked', user.is_blocked)
        user.save(update_fields=['is_allowed', 'is_blocked'])

        return user
