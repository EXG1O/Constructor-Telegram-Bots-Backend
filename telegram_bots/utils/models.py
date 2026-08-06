from django.apps import apps

from functools import cache
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..models import TelegramBot


@cache
def get_telegram_bot_modal() -> type[TelegramBot]:
    return apps.get_model('telegram_bots.TelegramBot')
