from django.db import models
from django.db.models import QuerySet
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

from django_stubs_ext.db.models import TypedModelMeta

from ..models import TelegramBot
from .service.client import ServiceClient

import secrets


class TelegramBotsHubManager(models.Manager['TelegramBotsHub']):
    def get_freest(self) -> TelegramBotsHub | None:
        return (
            sorted(hubs, key=lambda hub: hub.client.get_bot_ids())[0]
            if (hubs := self.all())
            else None
        )

    def get_bot_hub(self, bot_id: int) -> TelegramBotsHub:
        for hub in self.all():
            if bot_id in hub.client.get_bot_ids():
                return hub
        raise TelegramBotsHub.DoesNotExist()


def _generate_token() -> str:
    return secrets.token_hex(32)


class TelegramBotsHub(models.Model):
    url = models.CharField(_('URL-адрес'), max_length=255, unique=True)
    telegram_token = models.CharField(
        _('Telegram токен'), max_length=64, unique=True, default=_generate_token
    )
    service_token = models.CharField(
        _('Токен сервиса'), max_length=64, unique=True, default=_generate_token
    )
    microservice_token = models.CharField(
        _('Токен микросервиса'), max_length=64, unique=True, default=_generate_token
    )

    is_authenticated = True  # Stub for IsAuthenticated permission

    objects = TelegramBotsHubManager()

    class Meta(TypedModelMeta):
        db_table = 'telegram_bots_hub'
        verbose_name = _('Центр')
        verbose_name_plural = _('Центра')

    def __str__(self) -> str:
        return self.url

    @cached_property
    def client(self) -> ServiceClient:
        return ServiceClient(self.url, self.microservice_token)

    @property
    def telegram_bots(self) -> QuerySet[TelegramBot]:
        return TelegramBot.objects.filter(id__in=self.client.get_bot_ids())
