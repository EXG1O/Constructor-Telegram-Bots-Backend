from rest_framework import serializers

from ...models import Trigger, TriggerCommand, TriggerMessage, TriggerWebhook
from .connection import ConnectionSerializer


class TriggerCommandSerializer(serializers.ModelSerializer[TriggerCommand]):
    class Meta:
        model = TriggerCommand
        fields = ['command', 'payload', 'description']


class TriggerMessageSerializer(serializers.ModelSerializer[TriggerMessage]):
    class Meta:
        model = TriggerMessage
        fields = ['text']


class TriggerWebhookSerializer(serializers.ModelSerializer[TriggerWebhook]):
    class Meta:
        model = TriggerWebhook
        fields = []  # type: ignore [var-annotated]


class TriggerSerializer(serializers.ModelSerializer[Trigger]):
    command = TriggerCommandSerializer()
    message = TriggerMessageSerializer()
    webhook = TriggerWebhookSerializer()
    source_connections = ConnectionSerializer(many=True)

    class Meta:
        model = Trigger
        fields = ['id', 'command', 'message', 'webhook', 'source_connections']
