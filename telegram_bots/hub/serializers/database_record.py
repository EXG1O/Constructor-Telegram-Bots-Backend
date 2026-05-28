from rest_framework import fields, serializers

from constructor_telegram_bots.utils.deep_merge import deep_merge_data

from ...models import DatabaseRecord
from ...serializers.mixins import TelegramBotMixin

from typing import Any


class DatabaseRecordListSerializer(serializers.ListSerializer[list[DatabaseRecord]]):
    def run_validation(self, data: Any = fields.empty) -> dict[str, Any]:
        assert self.child
        return self.child.run_validation(data)

    def update(
        self, records: list[DatabaseRecord], validated_data: dict[str, Any]
    ) -> list[DatabaseRecord]:
        new_data: Any | None = validated_data.get('data')

        if new_data is None:
            return records

        for record in records:
            record.data = (
                deep_merge_data(record.data, new_data) if self.partial else new_data
            )

        DatabaseRecord.objects.bulk_update(records, fields=['data'])

        return records

    def save(self, **kwargs: Any) -> list[DatabaseRecord]:
        if self.instance is None:
            raise NotImplementedError("Bulk creation isn't implemented.")

        self.instance = self.update(self.instance, self.validated_data)
        return self.instance


class DatabaseRecordSerializer(
    TelegramBotMixin, serializers.ModelSerializer[DatabaseRecord]
):
    class Meta:
        model = DatabaseRecord
        fields = ['id', 'data']
        list_serializer_class = DatabaseRecordListSerializer

    def create(self, validated_data: dict[str, Any]) -> DatabaseRecord:
        return self.telegram_bot.database_records.create(**validated_data)

    def update(
        self, record: DatabaseRecord, validated_data: dict[str, Any]
    ) -> DatabaseRecord:
        new_data: Any | None = validated_data.get('data')

        if new_data is None:
            return record

        record.data = (
            deep_merge_data(record.data, new_data) if self.partial else new_data
        )
        record.save(update_fields=['data'])

        return record
