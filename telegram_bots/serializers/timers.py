from django.conf import settings

from constructor_telegram_bots.utils.serializers import validate_max_count

from ..models import Timer
from .base import BlockSerializer, DiagramSerializer
from .mixins import TelegramBotMixin

from typing import Any


class TimerSerializer(TelegramBotMixin, BlockSerializer[Timer]):
    class Meta(BlockSerializer.Meta):
        model = Timer
        fields = BlockSerializer.Meta.fields + ['duration_seconds']

    def validate(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self.instance:
            validate_max_count(
                self.telegram_bot.timers.count() + 1, settings.TELEGRAM_BOT_MAX_TIMERS
            )

        return data

    def create(self, validated_data: dict[str, Any]) -> Timer:
        return self.telegram_bot.timers.create(**validated_data)

    def update(self, timer: Timer, validated_data: dict[str, Any]) -> Timer:  # type: ignore[override]
        super().update(timer, validated_data, save=False)
        timer.duration_seconds = validated_data.get(
            'duration_seconds', timer.duration_seconds
        )
        timer.save(update_fields={*self._UPDATE_FIELDS, 'duration_seconds'})

        return timer


class DiagramTimerSerializer(DiagramSerializer[Timer]):
    class Meta(DiagramSerializer.Meta):
        model = Timer
        fields = DiagramSerializer.Meta.fields + ['duration_seconds']
        read_only_fields = DiagramSerializer.Meta.read_only_fields + [
            'duration_seconds'
        ]
