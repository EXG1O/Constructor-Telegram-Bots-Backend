from django.conf import settings

from rest_framework import fields, serializers

from constructor_telegram_bots.utils.deep_merge import deep_merge_data
from constructor_telegram_bots.utils.serializers import validate_max_count

from ...models import DatabaseRecord
from ...serializers.mixins import TelegramBotMixin

from typing import Any


class DatabaseRecordListSerializer(serializers.ListSerializer[list[DatabaseRecord]]):
    def run_validation(self, data: Any = fields.empty) -> dict[str, Any]:
        return self.run_child_validation(data)

    def update(
        self, records: list[DatabaseRecord], validated_data: dict[str, Any]
    ) -> list[DatabaseRecord]:
        data: Any | None = validated_data.get('data')

        for record in records:
            record.data = deep_merge_data(record.data, data) if self.partial else data

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

    def validate(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self.instance:
            validate_max_count(
                self.telegram_bot.database_records.count() + 1,
                settings.TELEGRAM_BOT_MAX_DATABASE_RECORDS,
            )

        return data

    def create(self, validated_data: dict[str, Any]) -> DatabaseRecord:
        return self.telegram_bot.database_records.create(**validated_data)

    def update(
        self, record: DatabaseRecord, validated_data: dict[str, Any]
    ) -> DatabaseRecord:
        data: Any | None = validated_data.get('data')

        record.data = deep_merge_data(record.data, data) if self.partial else data
        record.save(update_fields=['data'])

        return record
