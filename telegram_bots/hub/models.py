from django.conf import settings
from django.db import models
from django.db.models import Count
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

from django_stubs_ext.db.models import TypedModelMeta

from docker.errors import DockerException
from docker.models.containers import Container
from redis import Redis

from constructor_telegram_bots.docker import docker_client
from constructor_telegram_bots.utils.redis import get_redis_client

from .service.client import ServiceClient

from typing import TYPE_CHECKING, Any, cast
import secrets

if TYPE_CHECKING:
    from ..models import TelegramBot
else:
    TelegramBot = Any


def _generate_token() -> str:
    return secrets.token_hex(32)


class TelegramBotsHubManager(models.Manager['TelegramBotsHub']):
    def create_with_container(self) -> TelegramBotsHub:
        redis_client: Redis = get_redis_client()

        lock_key: str = 'tbh:lock:create_with_container:'
        result_key: str = 'tbh:shared_result:create_with_container'

        if TYPE_CHECKING:
            hub: TelegramBotsHub

        with redis_client.lock(lock_key, timeout=120, sleep=0.5):
            if cached_result := redis_client.get(result_key):
                hub = self.get(id=int(cast(Any, cached_result)))

                if len(hub.client.get_bot_ids()) < settings.TELEGRAM_BOTS_HUB_MAX_BOTS:
                    redis_client.expire(result_key, 6)
                    return hub

            telegram_token: str = _generate_token()
            service_token: str = _generate_token()
            microservice_token: str = _generate_token()

            container: Container = docker_client.containers.run(
                settings.TELEGRAM_BOTS_HUB_TAG,
                detach=True,
                restart_policy={'Name': 'on-failure', 'MaximumRetryCount': 3},
                environment={
                    'MODE': settings.MODE,
                    'REDIS_URL': settings.TELEGRAM_BOTS_HUB_REDIS_URL,
                    'SELF_TOKEN': microservice_token,
                    'TELEGRAM_TOKEN': telegram_token,
                    'SERVICE_URL': settings.SELF_URL,
                    'SERVICE_UNIX_SOCK': settings.SELF_UNIX_SOCK,
                    'SERVICE_TOKEN': service_token,
                },
                extra_hosts=(
                    {'host.docker.internal': 'host-gateway'}
                    if 'host.docker.internal' in settings.TELEGRAM_BOTS_HUB_REDIS_URL
                    else None
                ),
                volumes={
                    (
                        settings.TELEGRAM_BOTS_HUB_SOCKETS_VOLUME
                        or str(settings.SOCKETS_DIR)
                    ): {
                        'bind': '/app/sockets',
                        'mode': 'rw',
                    },
                    (
                        settings.TELEGRAM_BOTS_HUB_LOGS_VOLUME
                        or str(settings.LOGS_DIR / settings.TELEGRAM_BOTS_HUB_TAG)
                    ): {
                        'bind': '/app/logs',
                        'mode': 'rw',
                    },
                },
                network=settings.TELEGRAM_BOTS_HUB_NETWORK,
            )

            try:
                hub = self.create(
                    container_id=container.id,
                    telegram_token=telegram_token,
                    service_token=service_token,
                    microservice_token=microservice_token,
                )
            except Exception as create_error:
                try:
                    container.remove(force=True)
                except DockerException as docker_error:
                    raise docker_error from create_error
                raise create_error
            else:
                redis_client.set(result_key, hub.id, ex=6)
                return hub

    def get_freest(self) -> TelegramBotsHub:
        hub: TelegramBotsHub | None = (
            self.annotate(bot_count=Count('bots'))
            .filter(bot_count__lt=settings.TELEGRAM_BOTS_HUB_MAX_BOTS)
            .order_by('bot_count')
            .first()
        )

        if not hub:
            return self.create_with_container()

        return hub


class TelegramBotsHub(models.Model):
    container_id = models.CharField(_('ID контейнера'), max_length=255, unique=True)
    telegram_token = models.CharField(
        _('Telegram токен'), max_length=64, unique=True, default=_generate_token
    )
    service_token = models.CharField(
        _('Токен сервиса'), max_length=64, unique=True, default=_generate_token
    )
    microservice_token = models.CharField(
        _('Токен микросервиса'), max_length=64, unique=True, default=_generate_token
    )
    idle_start_date = models.DateTimeField(
        _('Дата начала простоя'), blank=True, null=True, auto_now_add=True
    )

    is_authenticated = True  # Stub for IsAuthenticated permission

    objects = TelegramBotsHubManager()

    if TYPE_CHECKING:
        bots: models.Manager[TelegramBot]

    class Meta(TypedModelMeta):
        db_table = 'telegram_bots_hub'
        verbose_name = _('Хаб')
        verbose_name_plural = _('Хабы')

    def __str__(self) -> str:
        return self.container_id

    @cached_property
    def container(self) -> Container:
        return docker_client.containers.get(self.container_id)

    @cached_property
    def client(self) -> ServiceClient:
        return ServiceClient(self.container_id, self.microservice_token)
