from django.conf import settings
from django.utils.translation import gettext as _

from rest_framework import serializers

from ..models import BackgroundTask
from .base import BlockSerializer, DiagramSerializer
from .mixins import TelegramBotMixin

from typing import Any


class BackgroundTaskSerializer(TelegramBotMixin, BlockSerializer[BackgroundTask]):
    class Meta(BlockSerializer.Meta):
        model = BackgroundTask
        fields = BlockSerializer.Meta.fields + ['interval']

    def validate(self, data: dict[str, Any]) -> dict[str, Any]:
        if (
            not self.instance
            and self.telegram_bot.background_tasks.count() + 1
            > settings.TELEGRAM_BOT_MAX_BACKGROUND_TASKS
        ):
            raise serializers.ValidationError(
                _('Нельзя добавлять больше %(max)s фоновых задач.')
                % {'max': settings.TELEGRAM_BOT_MAX_BACKGROUND_TASKS},
                code='max_limit',
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
        background_task.save(update_fields=self.update_fields + ['interval'])

        return background_task


class DiagramBackgroundTaskSerializer(DiagramSerializer[BackgroundTask]):
    class Meta(DiagramSerializer.Meta):
        model = BackgroundTask
        fields = DiagramSerializer.Meta.fields + ['interval']
        read_only_fields = DiagramSerializer.Meta.read_only_fields + ['interval']
