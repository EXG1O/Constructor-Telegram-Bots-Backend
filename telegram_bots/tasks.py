from celery import shared_task

from .hub.utils import get_telegram_bots_hub_modal
from .utils import get_telegram_bot_modal

from collections.abc import Generator
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .hub.models import TelegramBotsHub
    from .models import TelegramBot
else:
    TelegramBot = Any
    TelegramBotsHub = Any


@contextmanager
def telegram_bot_processing(telegram_bot_id: int) -> Generator[TelegramBot]:
    telegram_bot: TelegramBot = get_telegram_bot_modal().objects.get(id=telegram_bot_id)

    try:
        yield telegram_bot
    finally:
        telegram_bot.is_loading = False
        telegram_bot.save(update_fields=['is_loading'])


@shared_task
def start_telegram_bot(telegram_bot_id: int) -> None:
    with telegram_bot_processing(telegram_bot_id) as telegram_bot:
        hub: TelegramBotsHub | None = get_telegram_bots_hub_modal().objects.get_freest()

        if not hub:
            # FIXME: In the future, we plan to deploy a microservice if no free hub is ...
            # found, which will eliminate the need for this `raise`.
            raise RuntimeError()

        hub.client.start_bot(telegram_bot.id, telegram_bot.api_token)


@shared_task
def restart_telegram_bot(telegram_bot_id: int) -> None:
    with telegram_bot_processing(telegram_bot_id) as telegram_bot:
        telegram_bot.hub.client.restart_bot(telegram_bot.id)


@shared_task
def stop_telegram_bot(telegram_bot_id: int) -> None:
    with telegram_bot_processing(telegram_bot_id) as telegram_bot:
        telegram_bot.hub.client.stop_bot(telegram_bot.id)


@shared_task
def start_telegram_bots() -> None:
    for telegram_bot in get_telegram_bot_modal().objects.filter(must_be_enabled=True):
        if not telegram_bot.is_enabled:
            telegram_bot.start()
