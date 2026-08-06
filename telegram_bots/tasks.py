from celery import shared_task

from .hub.utils.models import get_telegram_bots_hub_modal

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .hub.models import TelegramBotsHub


@shared_task
def start_telegram_bot(id: int, token: str, webhook_url: str) -> None:
    hub: TelegramBotsHub = get_telegram_bots_hub_modal().objects.get_freest()

    with hub.get_client() as client:
        client.start_bot(id, token=token, webhook_url=webhook_url)


@shared_task
def restart_telegram_bot(id: int, token: str, webhook_url: str) -> None:
    hub: TelegramBotsHub = get_telegram_bots_hub_modal().objects.get(bots__id=id)

    with hub.get_client() as client:
        client.restart_bot(id, token=token, webhook_url=webhook_url)


@shared_task
def stop_telegram_bot(id: int) -> None:
    hub: TelegramBotsHub = get_telegram_bots_hub_modal().objects.get(bots__id=id)

    with hub.get_client() as client:
        client.stop_bot(id)
