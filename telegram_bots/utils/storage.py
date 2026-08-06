from django.apps import apps
from django.db.models import QuerySet

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from users.models import User

    from ..models import TelegramBot
    from ..models.base import AbstractMedia


def get_media_file_names_queryset[T: AbstractMedia](
    model: type[T], **filters: Any
) -> QuerySet[T, str]:
    return (
        model.objects.exclude(file='').filter(**filters).values_list('file', flat=True)  # type: ignore [attr-defined]
    )


def get_telegram_bot_file_names(
    owner: User | None = None, telegram_bot: TelegramBot | None = None
) -> set[str]:
    if TYPE_CHECKING:
        filter_key: str
        filter_value: User | TelegramBot

    if owner:
        filter_key = 'telegram_bot__owner'
        filter_value = owner
    elif telegram_bot:
        filter_key = 'telegram_bot'
        filter_value = telegram_bot
    else:
        raise ValueError('Either telegram_bot or owner must be provided.')

    message_filter = {f'message__{filter_key}': filter_value}
    invoice_filter = {f'invoice__{filter_key}': filter_value}

    return set(
        get_media_file_names_queryset(
            apps.get_model('telegram_bots.MessageImage'),
            **message_filter,
        ).union(
            get_media_file_names_queryset(
                apps.get_model('telegram_bots.MessageDocument'),
                **message_filter,
            ),
            get_media_file_names_queryset(
                apps.get_model('telegram_bots.InvoiceImage'),
                **invoice_filter,
            ),
        )
    )
