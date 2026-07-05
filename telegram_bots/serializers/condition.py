from django.conf import settings
from django.db import transaction
from django.utils.translation import gettext as _

from rest_framework import serializers

from ..models import Condition, ConditionPart
from .base import BlockSerializer, DiagramSerializer
from .mixins import TelegramBotMixin

from typing import Any


class ConditionPartSerializer(serializers.ModelSerializer[ConditionPart]):
    class Meta:
        model = ConditionPart
        fields = [
            'id',
            'type',
            'first_value',
            'operator',
            'second_value',
            'next_part_operator',
        ]


class ConditionSerializer(TelegramBotMixin, BlockSerializer[Condition]):
    parts = ConditionPartSerializer(many=True)

    class Meta(BlockSerializer.Meta):
        model = Condition
        fields = BlockSerializer.Meta.fields + ['parts']

    def validate_parts(self, data: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if not ((self.instance and self.partial) or data):
            raise serializers.ValidationError(
                _('Условие должно содержать хотя бы одну часть.'), code='empty'
            )

        if (
            self.instance.parts.count() + sum('id' not in item for item in data)
            if self.instance and self.partial
            else len(data)
        ) > settings.TELEGRAM_BOT_MAX_CONDITION_PARTS:
            raise serializers.ValidationError(
                _('Нельзя добавлять больше %(max)s частей условия.')
                % {'max': settings.TELEGRAM_BOT_MAX_CONDITION_PARTS},
                code='max_limit',
            )

        return data

    def validate(self, data: dict[str, Any]) -> dict[str, Any]:
        if (
            not self.instance
            and self.telegram_bot.conditions.count() + 1
            > settings.TELEGRAM_BOT_MAX_CONDITIONS
        ):
            raise serializers.ValidationError(
                _('Нельзя добавлять больше %(max)s условий.')
                % {'max': settings.TELEGRAM_BOT_MAX_CONDITIONS},
                code='max_limit',
            )

        return data

    def create_parts(
        self, condition: Condition, data: list[dict[str, Any]]
    ) -> list[ConditionPart]:
        create_parts: list[ConditionPart] = []

        for item in data:
            item.pop('id', None)
            create_parts.append(ConditionPart(condition=condition, **item))

        return ConditionPart.objects.bulk_create(create_parts)

    def create(self, validated_data: dict[str, Any]) -> Condition:
        parts_data: list[dict[str, Any]] = validated_data.pop('parts')

        with transaction.atomic():
            condition: Condition = self.telegram_bot.conditions.create(**validated_data)

            self.create_parts(condition, parts_data)

        return condition

    def update_parts(
        self, condition: Condition, data: list[dict[str, Any]] | None
    ) -> list[ConditionPart] | None:
        if not data:
            if not self.partial:
                condition.parts.all().delete()
            return None

        create_parts: list[ConditionPart] = []
        update_parts: list[ConditionPart] = []

        for item in data:
            try:
                part: ConditionPart = condition.parts.get(id=item.pop('id'))
            except KeyError, ConditionPart.DoesNotExist:
                create_parts.append(ConditionPart(condition=condition, **item))
            else:
                part.type = item.get('type', part.type)
                part.first_value = item.get('first_value', part.first_value)
                part.operator = item.get('operator', part.operator)
                part.second_value = item.get('second_value', part.second_value)
                part.next_part_operator = item.get(
                    'next_part_operator', part.next_part_operator
                )
                update_parts.append(part)

        new_parts: list[ConditionPart] = ConditionPart.objects.bulk_create(create_parts)
        ConditionPart.objects.bulk_update(
            update_parts,
            fields=[
                'type',
                'first_value',
                'operator',
                'second_value',
                'next_part_operator',
            ],
        )

        parts: list[ConditionPart] = new_parts + update_parts

        if not self.partial:
            condition.parts.exclude(id__in=[part.id for part in parts]).delete()

        return parts

    def update(self, condition: Condition, validated_data: dict[str, Any]) -> Condition:  # type: ignore[override]
        parts_data: list[dict[str, Any]] | None = validated_data.get('parts')

        with transaction.atomic():
            super().update(condition, validated_data, save=True)
            self.update_parts(condition, parts_data)

        return condition


class DiagramConditionSerializer(DiagramSerializer[Condition]):
    class Meta(DiagramSerializer.Meta):
        model = Condition
