from django.conf import settings
from django.db import transaction

from rest_framework import serializers

from drf_spectacular.extensions import OpenApiSerializerExtension
from drf_spectacular.openapi import AutoSchema
from drf_spectacular.plumbing import build_basic_type
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import Direction

from constructor_telegram_bots.utils.serializers import (
    validate_exclusive_fields,
    validate_max_count,
)

from ..models import Action, ActionDefaultKeyboardRemoval, ActionMessageDeletion
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


class ActionDefaultKeyboardRemovalSerializer(
    serializers.ModelSerializer[ActionDefaultKeyboardRemoval]
):
    class Meta:
        model = ActionDefaultKeyboardRemoval
        fields = []  # type: ignore [var-annotated]


class ActionDefaultKeyboardRemovalSerializerExtension(OpenApiSerializerExtension):  # type: ignore [no-untyped-call]
    target_class = ActionDefaultKeyboardRemovalSerializer

    def map_serializer(
        self, auto_schema: AutoSchema, direction: Direction
    ) -> dict[str, Any]:
        schema: dict[str, Any] | None = build_basic_type(OpenApiTypes.OBJECT)
        assert schema
        return schema


class ActionSerializer(TelegramBotMixin, BlockSerializer[Action]):
    message_deletion = ActionMessageDeletionSerializer(required=False, allow_null=True)
    default_keyboard_removal = ActionDefaultKeyboardRemovalSerializer(
        required=False, allow_null=True
    )

    class Meta(BlockSerializer.Meta):
        model = Action
        fields = BlockSerializer.Meta.fields + [
            'message_deletion',
            'default_keyboard_removal',
        ]

    def validate(self, data: dict[str, Any]) -> dict[str, Any]:
        has_message_deletion: bool = bool(data.get('message_deletion'))
        has_default_keyboard_removal: bool = (
            data.get('default_keyboard_removal') is not None
        )

        if self.instance and self.partial:
            if not has_message_deletion:
                with suppress(ActionMessageDeletion.DoesNotExist):
                    has_message_deletion = bool(self.instance.message_deletion)
            if not has_default_keyboard_removal:
                with suppress(ActionDefaultKeyboardRemoval.DoesNotExist):
                    has_default_keyboard_removal = bool(
                        self.instance.default_keyboard_removal
                    )

        validate_exclusive_fields(
            {
                'message_deletion': has_message_deletion,
                'default_keyboard_removal': has_default_keyboard_removal,
            }
        )

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

    def create_default_keyboard_removal(
        self, action: Action, data: dict[str, Any]
    ) -> ActionDefaultKeyboardRemoval:
        return ActionDefaultKeyboardRemoval.objects.create(action=action, **data)

    def create(self, validated_data: dict[str, Any]) -> Action:
        message_deletion_data: dict[str, Any] | None = validated_data.pop(
            'message_deletion', None
        )
        default_keyboard_removal_data: dict[str, Any] | None = validated_data.pop(
            'default_keyboard_removal', None
        )

        with transaction.atomic():
            action: Action = self.telegram_bot.actions.create(**validated_data)

            if message_deletion_data:
                self.create_message_deletion(action, message_deletion_data)
            if default_keyboard_removal_data is not None:
                self.create_default_keyboard_removal(
                    action, default_keyboard_removal_data
                )

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

    def update_default_keyboard_removal(
        self, action: Action, data: dict[str, Any] | None
    ) -> ActionDefaultKeyboardRemoval | None:
        if data is None:
            if not self.partial:
                with suppress(ActionDefaultKeyboardRemoval.DoesNotExist):
                    action.default_keyboard_removal.delete()
                    del action._state.fields_cache['default_keyboard_removal']
            return None

        try:
            return action.default_keyboard_removal
        except ActionDefaultKeyboardRemoval.DoesNotExist:
            return self.create_default_keyboard_removal(action, data)

    def update(self, action: Action, validated_data: dict[str, Any]) -> Action:  # type: ignore[override]
        message_deletion_data: dict[str, Any] | None = validated_data.get(
            'message_deletion'
        )
        default_keyboard_removal_data: dict[str, Any] | None = validated_data.get(
            'default_keyboard_removal'
        )

        with transaction.atomic():
            super().update(action, validated_data, save=True)
            self.update_message_deletion(action, message_deletion_data)
            self.update_default_keyboard_removal(action, default_keyboard_removal_data)

        return action


class DiagramActionSerializer(DiagramSerializer[Action]):
    class Meta(DiagramSerializer.Meta):
        model = Action
