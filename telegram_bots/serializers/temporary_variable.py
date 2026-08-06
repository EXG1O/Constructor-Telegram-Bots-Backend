from django.conf import settings

from constructor_telegram_bots.utils.serializers import validate_max_count

from ..models import TemporaryVariable
from .base import BlockSerializer, DiagramSerializer
from .mixins import TelegramBotMixin

from typing import Any


class TemporaryVariableSerializer(TelegramBotMixin, BlockSerializer[TemporaryVariable]):
    class Meta(BlockSerializer.Meta):
        model = TemporaryVariable
        fields = BlockSerializer.Meta.fields + ['value']

    def validate(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self.instance:
            validate_max_count(
                self.telegram_bot.temporary_variables.count() + 1,
                settings.TELEGRAM_BOT_MAX_TEMPORARY_VARIABLES,
            )

        return data

    def create(self, validated_data: dict[str, Any]) -> TemporaryVariable:
        return self.telegram_bot.temporary_variables.create(**validated_data)

    def update(  # type: ignore[override]
        self, temporary_variable: TemporaryVariable, validated_data: dict[str, Any]
    ) -> TemporaryVariable:
        super().update(temporary_variable, validated_data, save=False)
        temporary_variable.value = validated_data.get('value', temporary_variable.value)
        temporary_variable.save(update_fields={*self._UPDATE_FIELDS, 'value'})

        return temporary_variable


class DiagramTemporaryVariableSerializer(DiagramSerializer[TemporaryVariable]):
    class Meta(DiagramSerializer.Meta):
        model = TemporaryVariable
        fields = DiagramSerializer.Meta.fields + ['value']
        read_only_fields = DiagramSerializer.Meta.read_only_fields + ['value']
