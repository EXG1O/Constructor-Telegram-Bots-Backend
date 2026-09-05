from django.conf import settings
from django.db.models import QuerySet
from django.utils import timezone

from celery import shared_task

from platform_bot.models import PlatformBot
from platform_bot.service import (
    InlineKeyboard,
    InlineKeyboardButton,
    KeyboardButtonStyle,
    SendTelegramMessage,
    TextType,
)

from .enums import InvoiceStatus
from .models import Subscription, SubscriptionInvoice

from datetime import datetime
from math import ceil
from typing import TYPE_CHECKING, Final

_EXPIRY_NOTIFICATION_DAYS_TEMPLATE: Final[str] = """\
⏳ <b>Your Premium subscription expires in {days_left} days.</b>

✨ To keep access to all premium features, don't forget to renew your subscription.
"""
_EXPIRY_NOTIFICATION_HOURS_TEMPLATE: Final[str] = """\
🔥 <b>Your Premium subscription expires in {hours_left} hours!</b>

✨ To keep access to all premium features, don't forget to renew your subscription.
"""
_EXPIRY_NOTIFICATION_KEYBOARD: Final[InlineKeyboard] = InlineKeyboard(
    rows=[
        [
            InlineKeyboardButton(
                text='Renew Subscription',
                url=str(settings.APP_URL / 'premium/'),
                style=KeyboardButtonStyle.SUCCESS,
            )
        ]
    ]
)

_SUBSCRIPTION_EXPIRED_NOTIFICATION_TEXT: Final[str] = """\
⚠️ <b>Your Premium subscription has expired.</b>

❤️ <b>Thank you for being with us!</b> Your support made a real difference, and we hope to see you back soon.
"""
_SUBSCRIPTION_EXPIRED_NOTIFICATION_KEYBOARD: Final[InlineKeyboard] = InlineKeyboard(
    rows=[
        [
            InlineKeyboardButton(
                text='Restore Subscription',
                url=str(settings.APP_URL / 'premium/'),
                style=KeyboardButtonStyle.SUCCESS,
            )
        ]
    ]
)


@shared_task
def make_pending_invoices_expired() -> None:
    SubscriptionInvoice.objects.filter(
        status=InvoiceStatus.PENDING,
        created_date__lt=timezone.now() - settings.PREMIUM_INVOICE_PENDING_TIMEOUT,
    ).update(status=InvoiceStatus.EXPIRED)


@shared_task
def send_subscription_expiry_notifications() -> None:
    current_datetime: datetime = timezone.now()

    message_batch: list[SendTelegramMessage] = []

    if TYPE_CHECKING:
        owner_telegram_id: int
        end_date: datetime

    with PlatformBot().get_client() as client:
        for owner_telegram_id, end_date in (
            Subscription.objects.filter(
                end_date__gte=(
                    current_datetime
                    + settings.PREMIUM_SUBSCRIPTION_EXPIRY_NOTIFICATION_END
                ),
                end_date__lte=(
                    current_datetime
                    + settings.PREMIUM_SUBSCRIPTION_EXPIRY_NOTIFICATION_START
                ),
            )
            .values_list('owner__telegram_id', 'end_date')
            .iterator(chunk_size=500)
        ):
            hours_left: float = (end_date - current_datetime).total_seconds() / 3600
            message_batch.append(
                SendTelegramMessage(
                    chat_ids=[owner_telegram_id],
                    text=(
                        _EXPIRY_NOTIFICATION_DAYS_TEMPLATE.format(
                            days_left=ceil(hours_left / 24)
                        )
                        if hours_left > 48
                        else _EXPIRY_NOTIFICATION_HOURS_TEMPLATE.format(
                            hours_left=max(1, round(hours_left))
                        )
                    ),
                    text_type=TextType.HTML,
                    keyboard=_EXPIRY_NOTIFICATION_KEYBOARD,
                )
            )

            if len(message_batch) >= 100:
                client.send_telegram_messages(message_batch)
                message_batch.clear()

        if message_batch:
            client.send_telegram_messages(message_batch)


@shared_task
def delete_expired_subscriptions() -> None:
    expired_subscriptions: QuerySet[Subscription, tuple[int, int]] = (
        Subscription.objects.filter(end_date__lte=timezone.now()).values_list(
            'id', 'owner__telegram_id'
        )
    )

    if not expired_subscriptions.exists():
        return

    subscription_ids, owner_telegram_ids = zip(*expired_subscriptions, strict=True)

    with PlatformBot().get_client() as client:
        client.send_telegram_message(
            chat_ids=list(owner_telegram_ids),
            text=_SUBSCRIPTION_EXPIRED_NOTIFICATION_TEXT,
            text_type=TextType.HTML,
            keyboard=_SUBSCRIPTION_EXPIRED_NOTIFICATION_KEYBOARD,
        )

    Subscription.objects.filter(id__in=subscription_ids).delete()
