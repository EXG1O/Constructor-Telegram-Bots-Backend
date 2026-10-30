from django.conf import settings
from django.db import transaction

from rest_framework import serializers

from constructor_telegram_bots.utils.serializers import (
    validate_exclusive_fields,
    validate_max_count,
)

from ..models import Action, ActionMessageDeletion
from .base import BlockSerializer, DiagramSerializer
from .mixins import TelegramBotMixin

from contextlib import suppress
from typing import Any


class ActionMessageDeletionSerializer(
    serializers.ModelSerializer[ActionMessageDeletion]
):
    class Meta:
        model = ActionMessageDeletion
        fields = ['target']


class ActionSerializer(TelegramBotMixin, BlockSerializer[Action]):
    message_deletion = ActionMessageDeletionSerializer(required=False, allow_null=True)

    class Meta(BlockSerializer.Meta):
        model = Action
        fields = BlockSerializer.Meta.fields + ['message_deletion']

    def validate(self, data: dict[str, Any]) -> dict[str, Any]:
        has_message_deletion: bool = bool(data.get('message_deletion'))

        if self.instance and self.partial:  # noqa: SIM102 - future-proofing for more mutually exclusive fields
            if not has_message_deletion:
                with suppress(ActionMessageDeletion.DoesNotExist):
                    has_message_deletion = bool(self.instance.message_deletion)

        validate_exclusive_fields({'message_deletion': has_message_deletion})

        if not self.instance:
            validate_max_count(
                self.telegram_bot.actions.count() + 1,
                settings.TELEGRAM_BOT_MAX_ACTIONS,
            )

        return data

    def create_message_deletion(
        self, action: Action, data: dict[str, Any]
    ) -> ActionMessageDeletion:
        return ActionMessageDeletion.objects.create(action=action, **data)

    def create(self, validated_data: dict[str, Any]) -> Action:
        message_deletion_data: dict[str, Any] | None = validated_data.pop(
            'message_deletion', None
        )

        with transaction.atomic():
            action: Action = self.telegram_bot.actions.create(**validated_data)

            if message_deletion_data:
                self.create_message_deletion(action, message_deletion_data)

        return action

    def update_message_deletion(
        self, action: Action, data: dict[str, Any] | None
    ) -> ActionMessageDeletion | None:
        if not data:
            if not self.partial:
                with suppress(ActionMessageDeletion.DoesNotExist):
                    action.message_deletion.delete()
                    del action._state.fields_cache['message_deletion']
            return None

        try:
            message_deletion: ActionMessageDeletion = action.message_deletion
        except ActionMessageDeletion.DoesNotExist:
            return self.create_message_deletion(action, data)

        message_deletion.target = data.get('target', message_deletion.target)
        message_deletion.save(update_fields=['target'])

        return message_deletion

    def update(self, action: Action, validated_data: dict[str, Any]) -> Action:  # type: ignore[override]
        message_deletion_data: dict[str, Any] | None = validated_data.get(
            'message_deletion'
        )

        with transaction.atomic():
            super().update(action, validated_data, save=True)
            self.update_message_deletion(action, message_deletion_data)

        return action


class DiagramActionSerializer(DiagramSerializer[Action]):
    class Meta(DiagramSerializer.Meta):
        model = Action
