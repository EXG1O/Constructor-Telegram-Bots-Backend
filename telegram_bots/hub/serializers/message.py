from rest_framework import serializers

from ...models import (
    Message,
    MessageDocument,
    MessageImage,
    MessageKeyboard,
    MessageKeyboardButton,
    MessageSettings,
)
from ...serializers.base import MessageMediaSerializer
from .connection import ConnectionSerializer


class MessageSettingsSerializer(serializers.ModelSerializer[MessageSettings]):
    class Meta:
        model = MessageSettings
        fields = ['reply_to_user_message', 'send_as_new_message']


class MessageImageSerializer(MessageMediaSerializer[MessageImage]):
    class Meta(MessageMediaSerializer.Meta):
        model = MessageImage


class MessageDocumentSerializer(MessageMediaSerializer[MessageDocument]):
    class Meta(MessageMediaSerializer.Meta):
        model = MessageDocument


class MessageKeyboardButtonSerializer(
    serializers.ModelSerializer[MessageKeyboardButton]
):
    source_connections = ConnectionSerializer(many=True)

    class Meta:
        model = MessageKeyboardButton
        fields = ['id', 'row', 'position', 'text', 'url', 'style', 'source_connections']


class MessageKeyboardSerializer(serializers.ModelSerializer[MessageKeyboard]):
    buttons = MessageKeyboardButtonSerializer(many=True)

    class Meta:
        model = MessageKeyboard
        fields = ['type', 'buttons']


class MessageSerializer(serializers.ModelSerializer[Message]):
    settings = MessageSettingsSerializer()
    images = MessageImageSerializer(many=True)
    documents = MessageDocumentSerializer(many=True)
    keyboard = MessageKeyboardSerializer()
    source_connections = ConnectionSerializer(many=True)

    class Meta:
        model = Message
        fields = [
            'id',
            'text',
            'settings',
            'images',
            'documents',
            'keyboard',
            'source_connections',
        ]
