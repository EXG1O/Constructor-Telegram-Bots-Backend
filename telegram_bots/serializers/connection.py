from django.db.models import Model, QuerySet
from django.utils.translation import gettext as _

from rest_framework import serializers

from ..enums import ConnectionObjectType
from ..models import (
    APIRequest,
    BackgroundTask,
    Condition,
    Connection,
    DatabaseOperation,
    Invoice,
    Message,
    MessageKeyboardButton,
    Randomizer,
    TemporaryVariable,
    Timer,
    Trigger,
)
from .mixins import TelegramBotMixin

from collections.abc import Callable
from typing import Any, TypedDict


class _ObjectTypeConfig(TypedDict):
    model: type[Model]
    get_queryset: Callable[[ConnectionSerializer], QuerySet[Model]]


class ConnectionSerializer(TelegramBotMixin, serializers.ModelSerializer[Connection]):
    source_object_type = serializers.ChoiceField(
        choices=ConnectionObjectType.SOURCE_CHOICES
    )
    target_object_type = serializers.ChoiceField(
        choices=ConnectionObjectType.TARGET_CHOICES
    )

    class Meta:
        model = Connection
        fields = [
            'id',
            'source_object_type',
            'source_object_id',
            'source_handle_position',
            'target_object_type',
            'target_object_id',
            'target_handle_position',
        ]

    _object_type_map: dict[ConnectionObjectType, _ObjectTypeConfig] = {
        ConnectionObjectType.TRIGGER: _ObjectTypeConfig(
            model=Trigger, get_queryset=lambda self: self.telegram_bot.triggers.all()
        ),
        ConnectionObjectType.MESSAGE: _ObjectTypeConfig(
            model=Message, get_queryset=lambda self: self.telegram_bot.messages.all()
        ),
        ConnectionObjectType.MESSAGE_KEYBOARD_BUTTON: _ObjectTypeConfig(
            model=MessageKeyboardButton,
            get_queryset=lambda self: MessageKeyboardButton.objects.filter(
                keyboard__message__telegram_bot=self.telegram_bot
            ),
        ),
        ConnectionObjectType.CONDITION: _ObjectTypeConfig(
            model=Condition,
            get_queryset=lambda self: self.telegram_bot.conditions.all(),
        ),
        ConnectionObjectType.BACKGROUND_TASK: _ObjectTypeConfig(
            model=BackgroundTask,
            get_queryset=lambda self: self.telegram_bot.background_tasks.all(),
        ),
        ConnectionObjectType.API_REQUEST: _ObjectTypeConfig(
            model=APIRequest,
            get_queryset=lambda self: self.telegram_bot.api_requests.all(),
        ),
        ConnectionObjectType.DATABASE_OPERATION: _ObjectTypeConfig(
            model=DatabaseOperation,
            get_queryset=lambda self: self.telegram_bot.database_operations.all(),
        ),
        ConnectionObjectType.INVOICE: _ObjectTypeConfig(
            model=Invoice, get_queryset=lambda self: self.telegram_bot.invoices.all()
        ),
        ConnectionObjectType.TEMPORARY_VARIABLE: _ObjectTypeConfig(
            model=TemporaryVariable,
            get_queryset=lambda self: self.telegram_bot.temporary_variables.all(),
        ),
        ConnectionObjectType.TIMER: _ObjectTypeConfig(
            model=Timer, get_queryset=lambda self: self.telegram_bot.timers.all()
        ),
        ConnectionObjectType.RANDOMIZER: _ObjectTypeConfig(
            model=Randomizer,
            get_queryset=lambda self: self.telegram_bot.randomizers.all(),
        ),
    }

    def get_object(self, object_type: str, object_id: int) -> Model:
        object_type = ConnectionObjectType(object_type)
        config: _ObjectTypeConfig = self._object_type_map[object_type]

        try:
            return config['get_queryset'](self).get(id=object_id)
        except config['model'].DoesNotExist as error:  # type: ignore [attr-defined]
            raise serializers.ValidationError(
                _('%(object)s не найден.') % {'object': object_type.label},
                code='not_found',
            ) from error

    def validate(self, data: dict[str, Any]) -> dict[str, Any]:
        data['source_object'] = self.get_object(
            data.pop('source_object_type'), data.pop('source_object_id')
        )
        data['target_object'] = self.get_object(
            data.pop('target_object_type'), data.pop('target_object_id')
        )
        return data

    def create(self, validated_data: dict[str, Any]) -> Connection:
        return self.telegram_bot.connections.create(**validated_data)
