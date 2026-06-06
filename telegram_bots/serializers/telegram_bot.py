from rest_framework import serializers
from rest_framework.request import Request

from users.models import User as SiteUser

from ..models import TelegramBot

from typing import Any


class TelegramBotSerializer(serializers.ModelSerializer[TelegramBot]):
    class Meta:
        model = TelegramBot
        fields = [
            'id',
            'username',
            'api_token',
            'storage_size',
            'used_storage_size',
            'remaining_storage_size',
            'is_private',
            'is_enabled',
            'is_loading',
            'added_date',
        ]
        read_only_fields = [
            'id',
            'username',
            'storage_size',
            'used_storage_size',
            'remaining_storage_size',
            'is_enabled',
            'is_loading',
            'added_date',
        ]

    @property
    def site_user(self) -> SiteUser:
        request: Any = self.context.get('request')

        if not isinstance(request, Request):
            raise TypeError(
                'You not passed a rest_framework.request.Request instance '
                'as request to the serializer context.'
            )
        elif not isinstance(request.user, SiteUser):
            raise TypeError(
                'The request.user instance is not an users.models.User instance.'
            )

        return request.user

    def create(self, validated_data: dict[str, Any]) -> TelegramBot:
        bot = TelegramBot(owner=self.site_user, **validated_data)
        bot.update_username(save=False)
        bot.save()
        return bot

    def update(self, bot: TelegramBot, validated_data: dict[str, Any]) -> TelegramBot:
        old_token: str = bot.api_token
        new_token: str = validated_data.get('api_token', old_token)

        bot.api_token = new_token
        bot.is_private = validated_data.get('is_private', bot.is_private)
        bot.update_username(save=False)
        bot.save(update_fields=['username', 'api_token', 'is_private'])

        if new_token != old_token:
            bot.restart()

        return bot
