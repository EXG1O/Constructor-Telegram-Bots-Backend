from django.conf import settings

from rest_framework import serializers

from constructor_telegram_bots.utils.serializers import validate_max_count

from ..models import Variable
from .mixins import TelegramBotMixin

from typing import Any


class VariableSerializer(TelegramBotMixin, serializers.ModelSerializer[Variable]):
    class Meta:
        model = Variable
        fields = ['id', 'name', 'value', 'description']

    def validate(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self.instance:
            validate_max_count(
                self.telegram_bot.variables.count() + 1,
                settings.TELEGRAM_BOT_MAX_VARIABLES,
            )

        return data

    def create(self, validated_data: dict[str, Any]) -> Variable:
        return self.telegram_bot.variables.create(**validated_data)

    def update(self, variable: Variable, validated_data: dict[str, Any]) -> Variable:
        variable.name = validated_data.get('name', variable.name)
        variable.value = validated_data.get('value', variable.value)
        variable.description = validated_data.get('description', variable.description)
        variable.save(update_fields=['name', 'value', 'description'])

        return variable
