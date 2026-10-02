from rest_framework import serializers

from ...models import BackgroundTask
from .connection import ConnectionSerializer

from typing import Any


class BackgroundTaskSerializer(serializers.ModelSerializer[BackgroundTask]):
    source_connections = ConnectionSerializer(many=True)

    class Meta:
        model = BackgroundTask
        fields = ['id', 'status', 'interval', 'source_connections']
        read_only_fields = ['interval', 'source_connections']

    def update(
        self, task: BackgroundTask, validated_data: dict[str, Any]
    ) -> BackgroundTask:
        task.status = validated_data.get('status', task.status)
        task.save(update_fields=['status'])
        return task
