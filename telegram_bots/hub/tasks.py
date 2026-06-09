from django.conf import settings
from django.db.models import Count, QuerySet
from django.utils import timezone

from celery import shared_task
from docker.errors import DockerException

from constructor_telegram_bots.docker import docker_client

from ..models import TelegramBot
from .models import TelegramBotsHub
from .service.schemas import BotCredentials

from concurrent.futures import ThreadPoolExecutor
from contextlib import suppress
from itertools import batched
import concurrent.futures
import logging
import os

logger: logging.Logger = logging.getLogger(__name__)


def _delete_hub_docker_container(id: str) -> None:
    docker_client.containers.get(id).remove(force=True)
    os.remove(settings.SOCKETS_DIR / f'{id[:12]}.sock')


@shared_task
def ensure_idle_telegram_bots_hubs() -> None:
    TelegramBotsHub.objects.annotate(bot_count=Count('bots')).filter(
        bot_count=0, idle_start_date__isnull=True
    ).update(idle_start_date=timezone.now())


@shared_task
def delete_expired_telegram_bots_hubs() -> None:
    hubs: QuerySet[TelegramBotsHub] = TelegramBotsHub.objects.filter(
        idle_start_date__lt=timezone.now() - settings.TELEGRAM_BOTS_HUB_IDLE_TIMEOUT
    ).only('id', 'container_id')

    for hub in hubs:
        with suppress(DockerException, FileNotFoundError):
            _delete_hub_docker_container(hub.container_id)

    TelegramBotsHub.objects.filter(id__in=[hub.id for hub in hubs]).delete()


@shared_task
def sync_telegram_bots_hubs() -> None:
    docker_client.images.build(
        path=str(settings.TELEGRAM_BOTS_HUB_PATH),
        tag=settings.TELEGRAM_BOTS_HUB_TAG,
        rm=True,
    )

    with ThreadPoolExecutor(max_workers=12) as executor:
        concurrent.futures.wait(
            executor.submit(_delete_hub_docker_container, container_id)
            for container_id in TelegramBotsHub.objects.values_list(
                'container_id', flat=True
            )
        )

    TelegramBotsHub.objects.all().delete()

    for bots in batched(
        (
            TelegramBot.objects.filter(must_be_enabled=True)
            .only('id', 'api_token')
            .iterator(chunk_size=settings.TELEGRAM_BOTS_HUB_MAX_BOTS)
        ),
        settings.TELEGRAM_BOTS_HUB_MAX_BOTS,
        strict=False,
    ):
        bot_ids: list[int] = [bot.id for bot in bots]

        TelegramBot.objects.filter(id__in=bot_ids).update(is_loading=True)
        try:
            hub: TelegramBotsHub = TelegramBotsHub.objects.create_with_container()
            hub.client.start_bots(
                [
                    BotCredentials(
                        id=bot.id, token=bot.api_token, webhook_url=bot.webhook_url
                    )
                    for bot in bots
                ]
            )
        except Exception:
            logger.exception('Failed to start bots with IDs: %s', bot_ids)
