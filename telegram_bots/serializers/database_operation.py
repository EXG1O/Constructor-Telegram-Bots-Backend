from django.conf import settings
from django.db import transaction
from django.utils.translation import gettext as _

from rest_framework import serializers

from ..models import DatabaseCreateOperation, DatabaseOperation, DatabaseUpdateOperation
from .base import BlockSerializer, DiagramSerializer
from .mixins import TelegramBotMixin

from contextlib import suppress
from typing import Any


class DatabaseCreateOperationSerializer(
    serializers.ModelSerializer[DatabaseCreateOperation]
):
    class Meta:
        model = DatabaseCreateOperation
        fields = ['data']


class DatabaseUpdateOperationSerializer(
    serializers.ModelSerializer[DatabaseUpdateOperation]
):
    class Meta:
        model = DatabaseUpdateOperation
        fields = [
            'overwrite',
            'lookup_field_name',
            'lookup_field_value',
            'create_if_not_found',
            'new_data',
        ]


class DatabaseOperationSerializer(TelegramBotMixin, BlockSerializer[DatabaseOperation]):
    create_operation = DatabaseCreateOperationSerializer(
        required=False, allow_null=True
    )
    update_operation = DatabaseUpdateOperationSerializer(
        required=False, allow_null=True
    )

    class Meta(BlockSerializer.Meta):
        model = DatabaseOperation
        fields = BlockSerializer.Meta.fields + ['create_operation', 'update_operation']

    def validate(self, data: dict[str, Any]) -> dict[str, Any]:
        has_create_operation: bool = bool(data.get('create_operation'))
        has_update_operation: bool = bool(data.get('update_operation'))

        if self.instance and self.partial:
            if not has_create_operation:
                with suppress(DatabaseCreateOperation.DoesNotExist):
                    has_create_operation = bool(self.instance.create_operation)
            if not has_update_operation:
                with suppress(DatabaseUpdateOperation.DoesNotExist):
                    has_update_operation = bool(self.instance.update_operation)

        if has_create_operation is has_update_operation:
            raise serializers.ValidationError(
                _(
                    'Операция базы данных должна иметь значение только для одно из полей: '
                    "'create_operation' или 'update_operation'."
                ),
            )

        if (
            not self.instance
            and self.telegram_bot.database_operations.count() + 1
            > settings.TELEGRAM_BOT_MAX_DATABASE_OPERATIONS
        ):
            raise serializers.ValidationError(
                _('Нельзя добавлять больше %(max)s операций базы данных.')
                % {'max': settings.TELEGRAM_BOT_MAX_DATABASE_OPERATIONS},
                code='max_limit',
            )

        return data

    def create_create_operation(
        self, operation: DatabaseOperation, data: dict[str, Any]
    ) -> DatabaseCreateOperation:
        return DatabaseCreateOperation.objects.create(operation=operation, **data)

    def create_update_operation(
        self, operation: DatabaseOperation, data: dict[str, Any]
    ) -> DatabaseUpdateOperation:
        return DatabaseUpdateOperation.objects.create(operation=operation, **data)

    def create(self, validated_data: dict[str, Any]) -> DatabaseOperation:
        create_operation_data: dict[str, Any] | None = validated_data.pop(
            'create_operation', None
        )
        update_operation_data: dict[str, Any] | None = validated_data.pop(
            'update_operation', None
        )

        with transaction.atomic():
            operation: DatabaseOperation = self.telegram_bot.database_operations.create(
                **validated_data
            )

            if create_operation_data:
                self.create_create_operation(operation, create_operation_data)
            elif update_operation_data:
                self.create_update_operation(operation, update_operation_data)

        return operation

    def update_create_operation(
        self, operation: DatabaseOperation, data: dict[str, Any] | None
    ) -> DatabaseCreateOperation | None:
        if not data:
            if not self.partial:
                with suppress(DatabaseCreateOperation.DoesNotExist):
                    operation.create_operation.delete()
                    del operation._state.fields_cache['create_operation']
            return None

        try:
            create_operation: DatabaseCreateOperation = operation.create_operation
        except DatabaseCreateOperation.DoesNotExist:
            return self.create_create_operation(operation, data)

        create_operation.data = data.get('data', create_operation.data)
        create_operation.save(update_fields=['data'])

        return create_operation

    def update_update_operation(
        self, operation: DatabaseOperation, data: dict[str, Any] | None
    ) -> DatabaseUpdateOperation | None:
        if not data:
            if not self.partial:
                with suppress(DatabaseUpdateOperation.DoesNotExist):
                    operation.update_operation.delete()
                    del operation._state.fields_cache['update_operation']
            return None

        try:
            update_operation: DatabaseUpdateOperation = operation.update_operation
        except DatabaseUpdateOperation.DoesNotExist:
            return self.create_update_operation(operation, data)

        update_operation.overwrite = data.get('overwrite', update_operation.overwrite)
        update_operation.lookup_field_name = data.get(
            'lookup_field_name', update_operation.lookup_field_name
        )
        update_operation.lookup_field_value = data.get(
            'lookup_field_value', update_operation.lookup_field_value
        )
        update_operation.create_if_not_found = data.get(
            'create_if_not_found', update_operation.create_if_not_found
        )
        update_operation.new_data = data.get('new_data', update_operation.new_data)
        update_operation.save(
            update_fields=[
                'overwrite',
                'lookup_field_name',
                'lookup_field_value',
                'create_if_not_found',
                'new_data',
            ]
        )

        return update_operation

    def update(  # type: ignore[override]
        self, operation: DatabaseOperation, validated_data: dict[str, Any]
    ) -> DatabaseOperation:
        create_operation_data: dict[str, Any] | None = validated_data.get(
            'create_operation'
        )
        update_operation_data: dict[str, Any] | None = validated_data.get(
            'update_operation'
        )

        with transaction.atomic():
            super().update(operation, validated_data, save=True)
            self.update_create_operation(operation, create_operation_data)
            self.update_update_operation(operation, update_operation_data)

        return operation


class DiagramDatabaseOperationSerializer(DiagramSerializer[DatabaseOperation]):
    class Meta(DiagramSerializer.Meta):
        model = DatabaseOperation
