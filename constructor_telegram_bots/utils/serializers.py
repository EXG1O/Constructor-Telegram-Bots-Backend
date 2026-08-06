from django.utils.translation import gettext as _

from rest_framework import serializers


def validate_max_count(item_count: int, max_limit: int) -> None:
    if item_count > max_limit:
        raise serializers.ValidationError(
            _('Достигнут максимальный лимит: %(max)d.') % {'max': max_limit},
            code='max_limit',
        )


def validate_exclusive_fields(has_fields: dict[str, bool]) -> None:
    if list(has_fields.values()).count(True) != 1:
        raise serializers.ValidationError(
            _('Укажите значение только для одного из полей: %(fields)s.')
            % {'fields': ', '.join(f"'{key}'" for key in has_fields)},
        )
