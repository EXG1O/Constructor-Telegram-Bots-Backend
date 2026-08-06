from django.conf import settings
from django.db import transaction

from rest_framework import serializers

from constructor_telegram_bots.utils.serializers import (
    validate_exclusive_fields,
    validate_max_count,
)

from ..models import Trigger, TriggerCommand, TriggerMessage, TriggerWebhook
from .base import BlockSerializer, DiagramSerializer
from .mixins import TelegramBotMixin

from contextlib import suppress
from typing import Any


class TriggerCommandSerializer(serializers.ModelSerializer[TriggerCommand]):
    class Meta:
        model = TriggerCommand
        fields = ['command', 'payload', 'description']


class TriggerMessageSerializer(serializers.ModelSerializer[TriggerMessage]):
    class Meta:
        model = TriggerMessage
        fields = ['text']


class TriggerWebhookSerializer(serializers.ModelSerializer[TriggerWebhook]):
    url = serializers.SerializerMethodField()

    class Meta:
        model = TriggerWebhook
        fields = ['url']

    def get_url(self, webhook: TriggerWebhook) -> str:
        return webhook.get_webhook_url(request=self.context.get('request'))


class TriggerSerializer(TelegramBotMixin, BlockSerializer[Trigger]):
    command = TriggerCommandSerializer(required=False, allow_null=True)
    message = TriggerMessageSerializer(required=False, allow_null=True)
    webhook = TriggerWebhookSerializer(required=False, allow_null=True)

    class Meta(BlockSerializer.Meta):
        model = Trigger
        fields = BlockSerializer.Meta.fields + ['command', 'message', 'webhook']

    def validate(self, data: dict[str, Any]) -> dict[str, Any]:
        has_command: bool = bool(data.get('command'))
        has_message: bool = bool(data.get('message'))
        has_webhook: bool = data.get('webhook') is not None

        if self.instance and self.partial:
            if not has_command:
                with suppress(TriggerCommand.DoesNotExist):
                    has_command = bool(self.instance.command)
            if not has_message:
                with suppress(TriggerMessage.DoesNotExist):
                    has_message = bool(self.instance.message)
            if not has_webhook:
                with suppress(TriggerWebhook.DoesNotExist):
                    has_webhook = bool(self.instance.webhook)

        validate_exclusive_fields(
            {'command': has_command, 'message': has_message, 'webhook': has_webhook}
        )

        if not self.instance:
            validate_max_count(
                self.telegram_bot.triggers.count() + 1,
                settings.TELEGRAM_BOT_MAX_TRIGGERS,
            )

        return data

    def create_command(self, trigger: Trigger, data: dict[str, Any]) -> TriggerCommand:
        return TriggerCommand.objects.create(trigger=trigger, **data)

    def create_message(self, trigger: Trigger, data: dict[str, Any]) -> TriggerMessage:
        return TriggerMessage.objects.create(trigger=trigger, **data)

    def create_webhook(self, trigger: Trigger, data: dict[str, Any]) -> TriggerWebhook:
        return TriggerWebhook.objects.create(trigger=trigger, **data)

    def create(self, validated_data: dict[str, Any]) -> Trigger:
        command_data: dict[str, Any] | None = validated_data.pop('command', None)
        message_data: dict[str, Any] | None = validated_data.pop('message', None)
        webhook_data: dict[str, Any] | None = validated_data.pop('webhook', None)

        with transaction.atomic():
            trigger: Trigger = self.telegram_bot.triggers.create(**validated_data)

            if command_data:
                self.create_command(trigger, command_data)
            if message_data:
                self.create_message(trigger, message_data)
            if webhook_data is not None:
                self.create_webhook(trigger, webhook_data)

        return trigger

    def update_command(
        self, trigger: Trigger, data: dict[str, Any] | None
    ) -> TriggerCommand | None:
        if not data:
            if not self.partial:
                with suppress(TriggerCommand.DoesNotExist):
                    trigger.command.delete()
                    del trigger._state.fields_cache['command']
            return None

        try:
            command: TriggerCommand = trigger.command
        except TriggerCommand.DoesNotExist:
            return self.create_command(trigger, data)

        command.command = data.get('command', command.command)
        command.payload = data.get('payload', command.payload)
        command.description = data.get('description', command.description)
        command.save(update_fields=['command', 'payload', 'description'])

        return command

    def update_message(
        self, trigger: Trigger, data: dict[str, Any] | None
    ) -> TriggerMessage | None:
        if not data:
            if not self.partial:
                with suppress(TriggerMessage.DoesNotExist):
                    trigger.message.delete()
                    del trigger._state.fields_cache['message']
            return None

        try:
            message: TriggerMessage = trigger.message
        except TriggerMessage.DoesNotExist:
            return self.create_message(trigger, data)

        message.text = data.get('text', message.text)
        message.save(update_fields=['text'])

        return message

    def update_webhook(
        self, trigger: Trigger, data: dict[str, Any] | None
    ) -> TriggerWebhook | None:
        if data is None:
            if not self.partial:
                with suppress(TriggerWebhook.DoesNotExist):
                    trigger.webhook.delete()
                    del trigger._state.fields_cache['webhook']
            return None

        try:
            webhook: TriggerWebhook = trigger.webhook
        except TriggerWebhook.DoesNotExist:
            return self.create_webhook(trigger, data)

        return webhook

    def update(self, trigger: Trigger, validated_data: dict[str, Any]) -> Trigger:  # type: ignore[override]
        command_data: dict[str, Any] | None = validated_data.get('command')
        message_data: dict[str, Any] | None = validated_data.get('message')
        webhook_data: dict[str, Any] | None = validated_data.get('webhook')

        with transaction.atomic():
            super().update(trigger, validated_data, save=True)
            self.update_command(trigger, command_data)
            self.update_message(trigger, message_data)
            self.update_webhook(trigger, webhook_data)

        return trigger


class DiagramTriggerSerializer(DiagramSerializer[Trigger]):
    class Meta(DiagramSerializer.Meta):
        model = Trigger
