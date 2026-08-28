from django.utils import timezone

from rest_framework import serializers

from ...models import User
from ...serializers.mixins import TelegramBotMixin

from typing import Any


class UserSerializer(TelegramBotMixin, serializers.ModelSerializer[User]):
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
        ]
        read_only_fields = ['is_allowed', 'is_blocked']

    def create(self, validated_data: dict[str, Any]) -> User:
        telegram_id: int = validated_data.pop('telegram_id')

        create_defaults: dict[str, Any] = validated_data.copy()
        update_defaults: dict[str, Any] = validated_data.copy()
        update_defaults['last_activity_date'] = timezone.now

        user, created = self.telegram_bot.users.update_or_create(
            telegram_id=telegram_id,
            create_defaults=create_defaults,
            defaults=update_defaults,
        )
        return user
