from django.conf import settings

from constructor_telegram_bots.utils.serializers import validate_max_count

from ..models import Randomizer
from .base import BlockSerializer, DiagramSerializer
from .mixins import TelegramBotMixin

from typing import Any


class RandomizerSerializer(TelegramBotMixin, BlockSerializer[Randomizer]):
    class Meta(BlockSerializer.Meta):
        model = Randomizer

    def validate(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self.instance:
            validate_max_count(
                self.telegram_bot.randomizers.count() + 1,
                settings.TELEGRAM_BOT_MAX_RANDOMIZERS,
            )

        return data

    def create(self, validated_data: dict[str, Any]) -> Randomizer:
        return self.telegram_bot.randomizers.create(**validated_data)


class DiagramRandomizerSerializer(DiagramSerializer[Randomizer]):
    class Meta(DiagramSerializer.Meta):
        model = Randomizer
        fields = DiagramSerializer.Meta.fields
        read_only_fields = DiagramSerializer.Meta.read_only_fields
