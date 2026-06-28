from celery import shared_task

from .hub.utils.models import get_telegram_bots_hub_modal

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .hub.models import TelegramBotsHub
    from .models import TelegramBot
else:
    TelegramBot = Any
    TelegramBotsHub = Any


@shared_task
def start_telegram_bot(id: int, token: str, webhook_url: str) -> None:
    hub: TelegramBotsHub = get_telegram_bots_hub_modal().objects.get_freest()
    hub.client.start_bot(id, token=token, webhook_url=webhook_url)


@shared_task
def restart_telegram_bot(id: int, token: str, webhook_url: str) -> None:
    hub: TelegramBotsHub = get_telegram_bots_hub_modal().objects.get(bots__id=id)
    hub.client.restart_bot(id, token=token, webhook_url=webhook_url)


@shared_task
def stop_telegram_bot(id: int) -> None:
    hub: TelegramBotsHub = get_telegram_bots_hub_modal().objects.get(bots__id=id)
    hub.client.stop_bot(id)
