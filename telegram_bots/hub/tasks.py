from django.conf import settings
from django.db.models import Count, Q, QuerySet
from django.utils import timezone

from celery import shared_task

from constructor_telegram_bots.docker import docker_client

from ..models import TelegramBot
from .models import TelegramBotsHub
from .service import BotCredentials
from .utils.hubs import force_delete_all_hubs, force_delete_hub_docker_container

from itertools import batched
from typing import TYPE_CHECKING
import logging

logger: logging.Logger = logging.getLogger(__name__)


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
        force_delete_hub_docker_container(hub.container_id)

    TelegramBotsHub.objects.filter(id__in=[hub.id for hub in hubs]).delete()


def _start_telegram_bots(is_premium: bool) -> None:
    queryset: QuerySet[TelegramBot] = TelegramBot.objects.filter(must_be_enabled=True)

    if TYPE_CHECKING:
        max_bot_count_per_hub: int

    if is_premium:
        queryset = queryset.filter(owner__subscription__expiry_date__gt=timezone.now())
        max_bot_count_per_hub = settings.TELEGRAM_BOTS_HUB_PREMIUM_MAX_BOTS
    else:
        queryset = queryset.filter(
            Q(owner__subscription__isnull=True)
            | Q(owner__subscription__expiry_date__lte=timezone.now())
        )
        max_bot_count_per_hub = settings.TELEGRAM_BOTS_HUB_DEFAULT_MAX_BOTS

    for bots in batched(
        queryset.only('id', 'api_token').iterator(chunk_size=1000),
        max_bot_count_per_hub,
        strict=False,
    ):
        bot_ids: set[int] = {bot.id for bot in bots}

        TelegramBot.objects.filter(id__in=bot_ids).update(is_loading=True)
        try:
            hub: TelegramBotsHub = TelegramBotsHub.objects.create_with_container(
                is_premium=is_premium
            )

            with hub.get_client() as client:
                client.start_bots(
                    [
                        BotCredentials(
                            id=bot.id, token=bot.api_token, webhook_url=bot.webhook_url
                        )
                        for bot in bots
                    ]
                )
        except Exception:
            logger.exception('Failed to start bots with IDs: %s', bot_ids)


@shared_task
def sync_telegram_bots_hubs() -> None:
    docker_client.images.build(
        path=str(settings.TELEGRAM_BOTS_HUB_PATH),
        tag=settings.TELEGRAM_BOTS_HUB_TAG,
        rm=True,
    )

    force_delete_all_hubs()

    _start_telegram_bots(is_premium=True)
    _start_telegram_bots(is_premium=False)
