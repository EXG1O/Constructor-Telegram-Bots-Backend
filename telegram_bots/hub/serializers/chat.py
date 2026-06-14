from django.db.models import Q
from django.utils.translation import gettext as _

from rest_framework import serializers

from ...models import Chat, User
from ...serializers.mixins import TelegramBotMixin

from typing import Any


class ChatUserSerializer(serializers.ModelSerializer[User]):
    class Meta:
        model = User
        fields = ['id', 'telegram_id']
        extra_kwargs = {
            'id': {'read_only': False, 'required': False},
            'telegram_id': {'required': False},
        }


class ChatSerializer(TelegramBotMixin, serializers.ModelSerializer[Chat]):
    users = ChatUserSerializer(many=True, write_only=True)

    class Meta:
        model = Chat
        fields = [
            'id',
            'telegram_id',
            'type',
            'title',
            'username',
            'first_name',
            'last_name',
            'is_forum',
            'is_direct_messages',
            'users',
        ]

    def validate_users(self, data: list[dict[str, Any]]) -> list[User]:
        ids: set[int] = set()
        telegram_ids: set[int] = set()

        for item in data:
            if id := item.get('id'):
                ids.add(id)
            elif telegram_id := item.get('telegram_id'):
                telegram_ids.add(telegram_id)

        if not (ids or telegram_ids):
            raise serializers.ValidationError(
                _("Укажите значение для полей 'id' или 'telegram_id'.")
            )

        users: list[User] = list(
            User.objects.filter(Q(id__in=ids) | Q(telegram_id__in=telegram_ids))
        )

        if not users:
            raise serializers.ValidationError(
                _('Пользователи не найдены.'), code='not_found'
            )

        return users

    def create(self, validated_data: dict[str, Any]) -> Chat:
        telegram_id: int = validated_data.pop('telegram_id')
        users: list[User] = validated_data.pop('users')

        chat, created = self.telegram_bot.chats.get_or_create(
            telegram_id=telegram_id, defaults=validated_data
        )

        if not created:
            chat.type = validated_data.get('type', chat.type)
            chat.title = validated_data.get('title', chat.title)
            chat.username = validated_data.get('username', chat.username)
            chat.first_name = validated_data.get('first_name', chat.first_name)
            chat.last_name = validated_data.get('last_name', chat.last_name)
            chat.is_forum = validated_data.get('is_forum', chat.is_forum)
            chat.is_direct_messages = validated_data.get(
                'is_direct_messages', chat.is_direct_messages
            )
            chat.save(
                update_fields=[
                    'type',
                    'title',
                    'username',
                    'first_name',
                    'last_name',
                    'is_forum',
                    'is_direct_messages',
                ]
            )

        chat.users.add(*users)

        return chat
