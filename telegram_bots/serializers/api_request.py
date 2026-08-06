from django.conf import settings
from django.utils.translation import gettext as _

from rest_framework import serializers

from constructor_telegram_bots.utils.serializers import validate_max_count

from ..models import APIRequest
from .base import BlockSerializer, DiagramSerializer
from .mixins import TelegramBotMixin

from typing import Any


class APIRequestSerializer(TelegramBotMixin, BlockSerializer[APIRequest]):
    class Meta(BlockSerializer.Meta):
        model = APIRequest
        fields = BlockSerializer.Meta.fields + ['url', 'method', 'headers', 'body']

    def validate_headers(self, data: list[Any] | dict[str, Any]) -> dict[str, str]:
        if not isinstance(data, dict):
            raise serializers.ValidationError(_('Заголовки должны быть словарём.'))

        for key, value in data.items():
            if not isinstance(value, str):
                raise serializers.ValidationError(
                    _("Значение для заголовка '%(key)s' должно быть строкой.")
                    % {'key': key}
                )

        return data

    def validate(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self.instance:
            validate_max_count(
                self.telegram_bot.api_requests.count() + 1,
                settings.TELEGRAM_BOT_MAX_API_REQUESTS,
            )

        return data

    def create(self, validated_data: dict[str, Any]) -> APIRequest:
        return self.telegram_bot.api_requests.create(**validated_data)

    def update(  # type: ignore[override]
        self, api_request: APIRequest, validated_data: dict[str, Any]
    ) -> APIRequest:
        super().update(api_request, validated_data, save=False)
        api_request.url = validated_data.get('url', api_request.url)
        api_request.method = validated_data.get('method', api_request.method)
        api_request.headers = validated_data.get('headers', api_request.headers)
        api_request.body = validated_data.get('body', api_request.body)
        api_request.save(
            update_fields={*self._UPDATE_FIELDS, 'url', 'method', 'headers', 'body'}
        )

        return api_request


class DiagramAPIRequestSerializer(DiagramSerializer[APIRequest]):
    class Meta(DiagramSerializer.Meta):
        model = APIRequest
        fields = DiagramSerializer.Meta.fields + ['url', 'method']
        read_only_fields = DiagramSerializer.Meta.read_only_fields + ['url', 'method']
