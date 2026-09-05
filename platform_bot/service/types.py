from .enums import TextType
from .models import DefaultKeyboard, InlineKeyboard, LinkPreviewOptions

from typing import NotRequired, TypedDict


class SendTelegramMessage(TypedDict):
    chat_ids: list[int]
    text: str
    text_type: NotRequired[TextType]
    link_preview_options: NotRequired[LinkPreviewOptions]
    keyboard: NotRequired[DefaultKeyboard | InlineKeyboard]
    disable_notification: NotRequired[bool]
    protect_content: NotRequired[bool]
