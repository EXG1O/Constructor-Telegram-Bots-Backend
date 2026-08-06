from django.conf import settings

from constructor_telegram_bots.utils.serializers import validate_max_count

from ..models import BackgroundTask
from .base import BlockSerializer, DiagramSerializer
from .mixins import TelegramBotMixin

from typing import Any


class BackgroundTaskSerializer(TelegramBotMixin, BlockSerializer[BackgroundTask]):
    class Meta(BlockSerializer.Meta):
        model = BackgroundTask
        fields = BlockSerializer.Meta.fields + ['interval']

    def validate(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self.instance:
            validate_max_count(
                self.telegram_bot.background_tasks.count() + 1,
                settings.TELEGRAM_BOT_MAX_BACKGROUND_TASKS,
            )

        return data

    def create(self, validated_data: dict[str, Any]) -> BackgroundTask:
        return self.telegram_bot.background_tasks.create(**validated_data)

    def update(  # type: ignore[override]
        self, background_task: BackgroundTask, validated_data: dict[str, Any]
    ) -> BackgroundTask:
        super().update(background_task, validated_data, save=False)
        background_task.interval = validated_data.get(
            'interval', background_task.interval
        )
        background_task.save(update_fields={*self._UPDATE_FIELDS, 'interval'})

        return background_task


class DiagramBackgroundTaskSerializer(DiagramSerializer[BackgroundTask]):
    class Meta(DiagramSerializer.Meta):
        model = BackgroundTask
        fields = DiagramSerializer.Meta.fields + ['interval']
        read_only_fields = DiagramSerializer.Meta.read_only_fields + ['interval']
