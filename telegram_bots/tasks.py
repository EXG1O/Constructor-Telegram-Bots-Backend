from django.conf import settings

from celery import shared_task

from .hub.utils.models import get_telegram_bots_hub_model
from .utils.models import get_telegram_bot_model

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .hub.models import TelegramBotsHub
    from .hub.service import Client


@shared_task
def start_telegram_bot(id: int, token: str, webhook_url: str, is_premium: bool) -> None:
    hub: TelegramBotsHub = get_telegram_bots_hub_model().objects.get_freest(
        is_premium=is_premium
    )

    with hub.get_client() as client:
        client.start_bot(id, token=token, webhook_url=webhook_url)


@shared_task
def restart_telegram_bot(id: int, token: str, webhook_url: str) -> None:
    hub: TelegramBotsHub = get_telegram_bots_hub_model().objects.get(bots__id=id)

    with hub.get_client() as client:
        client.restart_bot(id, token=token, webhook_url=webhook_url)


@shared_task
def stop_telegram_bot(id: int) -> None:
    hub: TelegramBotsHub = get_telegram_bots_hub_model().objects.get(bots__id=id)

    with hub.get_client() as client:
        client.stop_bot(id)


@shared_task
def migrate_telegram_bots(owner_id: int, target_hub_is_premium: bool) -> None:
    target_hub: TelegramBotsHub | None = None
    target_hub_client: Client | None = None
    target_hub_max_bot_count: int = (
        settings.TELEGRAM_BOTS_HUB_PREMIUM_MAX_BOTS
        if target_hub_is_premium
        else settings.TELEGRAM_BOTS_HUB_DEFAULT_MAX_BOTS
    )

    try:
        for bot in (
            get_telegram_bot_model()
            .objects.select_related('hub')
            .filter(owner__id=owner_id, hub__is_premium=not target_hub_is_premium)
            .iterator(chunk_size=250)
        ):
            current_hub: TelegramBotsHub | None = bot.hub

            if not current_hub:
                continue

            with current_hub.get_client() as client:
                client.stop_bot(bot.id)

            if (
                target_hub
                and target_hub_client
                and len(target_hub_client.get_bot_ids()) >= target_hub_max_bot_count
            ):
                target_hub_client.close()
                target_hub = None
                target_hub_client = None

            if not target_hub or not target_hub_client:
                target_hub = get_telegram_bots_hub_model().objects.get_freest(
                    is_premium=target_hub_is_premium
                )
                target_hub_client = target_hub.get_client()

            target_hub_client.start_bot(
                bot.id, token=bot.api_token, webhook_url=bot.webhook_url
            )
    finally:
        if target_hub_client:
            target_hub_client.close()
