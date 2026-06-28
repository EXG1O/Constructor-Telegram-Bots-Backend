from django.apps import apps

from functools import cache
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..models import TelegramBotsHub
else:
    TelegramBotsHub = Any


@cache
def get_telegram_bots_hub_modal() -> type[TelegramBotsHub]:
    return apps.get_model('telegram_bots_hub.TelegramBotsHub')
