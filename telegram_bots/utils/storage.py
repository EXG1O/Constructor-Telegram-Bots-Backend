from django.apps import apps

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from users.models import User

    from ..models import InvoiceImage, MessageDocument, MessageImage, TelegramBot


def get_telegram_bot_file_names(
    owner: User | None = None,
    telegram_bot: TelegramBot | None = None,
) -> set[str]:
    if not (owner or telegram_bot):
        raise ValueError('Either telegram_bot or owner must be provided.')

    message_image_model: type[MessageImage] = apps.get_model(
        'telegram_bots.MessageImage'
    )
    message_document_model: type[MessageDocument] = apps.get_model(
        'telegram_bots.MessageDocument'
    )
    invoice_image_model: type[InvoiceImage] = apps.get_model(
        'telegram_bots.InvoiceImage'
    )

    if TYPE_CHECKING:
        message_filter: dict[str, Any]
        invoice_filter: dict[str, Any]

    if telegram_bot:
        message_filter = {'message__telegram_bot': telegram_bot}
        invoice_filter = {'invoice__telegram_bot': telegram_bot}
    else:
        message_filter = {'message__telegram_bot__owner': owner}
        invoice_filter = {'invoice__telegram_bot__owner': owner}

    return set(
        message_image_model.objects.exclude(file='')  # type: ignore [arg-type]
        .filter(**message_filter)
        .values_list('file', flat=True)
        .union(
            message_document_model.objects.exclude(file='')
            .filter(**message_filter)
            .values_list('file', flat=True),
            invoice_image_model.objects.exclude(file='')
            .filter(**invoice_filter)
            .values_list('file', flat=True),
        )
    )
