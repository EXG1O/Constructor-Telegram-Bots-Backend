from rest_framework import serializers

from ..models import Chat

from typing import Any


class ChatSerializer(serializers.ModelSerializer[Chat]):
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
        read_only_fields = [
            'telegram_id',
            'type',
            'title',
            'username',
            'first_name',
            'last_name',
            'is_forum',
            'is_direct_messages',
        ]

    def update(self, chat: Chat, validated_data: dict[str, Any]) -> Chat:
        chat.is_allowed = validated_data.get('is_allowed', chat.is_allowed)
        chat.is_blocked = validated_data.get('is_blocked', chat.is_blocked)
        chat.save(update_fields=['is_allowed', 'is_blocked'])

        return chat
