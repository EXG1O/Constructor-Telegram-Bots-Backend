from telegram_bots.utils.storage import get_telegram_bot_file_names

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..models import User


def get_user_file_names(user: User) -> set[str]:
    return get_telegram_bot_file_names(owner=user)
