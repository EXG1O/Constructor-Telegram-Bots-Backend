from .models import DefaultKeyboard, InlineKeyboard, LinkPreviewOptions
from .types import SendTelegramMessage

from typing import Any, Unpack


def build_send_telegram_message_payload(
    **kwargs: Unpack[SendTelegramMessage],
) -> dict[str, Any]:
    keyboard: DefaultKeyboard | InlineKeyboard | None = kwargs.get('keyboard')

    return {
        'chat_ids': kwargs['chat_ids'],
        'text': kwargs['text'],
        'text_type': kwargs.get('text_type'),
        'link_preview_options': kwargs.get(
            'link_preview_options', LinkPreviewOptions(is_disabled=True)
        ).model_dump(),
        'default_keyboard': (
            keyboard.model_dump() if isinstance(keyboard, DefaultKeyboard) else None
        ),
        'inline_keyboard': (
            keyboard.model_dump() if isinstance(keyboard, InlineKeyboard) else None
        ),
        'disable_notification': kwargs.get('disable_notification', False),
        'protect_content': kwargs.get('protect_content', False),
    }
