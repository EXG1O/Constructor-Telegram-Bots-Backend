from django.db.models import Q, QuerySet
from django.utils.translation import gettext as _

from rest_framework import serializers

from ...models import Chat, User
from ...serializers.mixins import TelegramBotMixin

from typing import Any


class ChatSerializer(TelegramBotMixin, serializers.ModelSerializer[Chat]):
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
            'is_allowed',
            'is_blocked',
        ]
        read_only_fields = ['is_allowed', 'is_blocked']

    def create(self, validated_data: dict[str, Any]) -> Chat:
        chat, created = self.telegram_bot.chats.update_or_create(
            telegram_id=validated_data.pop('telegram_id'), defaults=validated_data
        )
        return chat


class ChatUserListSerializer(serializers.ListSerializer[User]):
    def validate(self, data: list[dict[str, Any]]) -> QuerySet[User]:
        ids: set[int] = set()
        telegram_ids: set[int] = set()
        errors: dict[str, str] = {}

        for index, item in enumerate(data):
            if id := item.get('id'):
                ids.add(id)
            elif telegram_id := item.get('telegram_id'):
                telegram_ids.add(telegram_id)
            else:
                errors[str(index)] = _(
                    "Укажите значение для полей 'id' или 'telegram_id'."
                )

        if errors:
            raise serializers.ValidationError(errors)

        users: QuerySet[User] = User.objects.filter(
            Q(id__in=ids) | Q(telegram_id__in=telegram_ids)
        )

        if not users.exists():
            raise serializers.ValidationError(
                _('Пользователи не найдены.'), code='not_found'
            )

        return users


class ChatUserSerializer(serializers.ModelSerializer[User]):
    class Meta:
        model = User
        fields = ['id', 'telegram_id']
        extra_kwargs = {
            'id': {'read_only': False, 'required': False},
            'telegram_id': {'required': False},
        }
        list_serializer_class = ChatUserListSerializer
