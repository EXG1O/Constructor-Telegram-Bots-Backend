from rest_framework import fields, serializers

from ...models import BackgroundTask
from .connection import ConnectionSerializer

from typing import Any


class BackgroundTaskListSerializer(serializers.ListSerializer[list[BackgroundTask]]):
    def run_validation(self, data: Any = fields.empty) -> dict[str, Any]:
        return self.run_child_validation(data)

    def update(
        self, tasks: list[BackgroundTask], validated_data: dict[str, Any]
    ) -> list[BackgroundTask]:
        status: str | None = validated_data.get('status')

        for task in tasks:
            task.status = status or task.status

        BackgroundTask.objects.bulk_update(tasks, fields=['status'])
        return tasks

    def save(self, **kwargs: Any) -> list[BackgroundTask]:
        if self.instance is None:
            raise NotImplementedError("Bulk creation isn't implemented.")

        self.instance = self.update(self.instance, self.validated_data)
        return self.instance


class BackgroundTaskSerializer(serializers.ModelSerializer[BackgroundTask]):
    source_connections = ConnectionSerializer(many=True)

    class Meta:
        model = BackgroundTask
        fields = ['id', 'status', 'interval', 'source_connections']
        read_only_fields = ['interval', 'source_connections']
        list_serializer_class = BackgroundTaskListSerializer

    def update(
        self, task: BackgroundTask, validated_data: dict[str, Any]
    ) -> BackgroundTask:
        task.status = validated_data.get('status', task.status)
        task.save(update_fields=['status'])
        return task
