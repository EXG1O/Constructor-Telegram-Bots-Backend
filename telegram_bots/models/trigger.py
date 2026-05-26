from django.db import models
from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _

from django_stubs_ext.db.models import TypedModelMeta

from .base import AbstractBlock

from typing import TYPE_CHECKING
import secrets


class TriggerCommand(models.Model):
    trigger = models.OneToOneField(
        'Trigger',
        on_delete=models.CASCADE,
        related_name='command',
        verbose_name=_('Триггер'),
    )
    command = models.CharField(_('Команда'), max_length=32)
    payload = models.CharField(
        _('Полезная нагрузка'), max_length=64, blank=True, null=True
    )
    description = models.CharField(_('Описание'), max_length=255, blank=True, null=True)

    class Meta(TypedModelMeta):
        db_table = 'telegram_bot_trigger_command'
        indexes = [
            models.Index(fields=['command']),
            models.Index(fields=['payload']),
            models.Index(fields=['description']),
        ]
        verbose_name = _('Команда триггер')
        verbose_name_plural = _('Команды триггеры')

    def __str__(self) -> str:
        return self.command


class TriggerMessage(models.Model):
    trigger = models.OneToOneField(
        'Trigger',
        on_delete=models.CASCADE,
        related_name='message',
        verbose_name=_('Триггер'),
    )
    text = models.TextField(_('Текст'), max_length=4096, null=True)

    class Meta(TypedModelMeta):
        db_table = 'telegram_bot_trigger_message'
        verbose_name = _('Сообщение триггер')
        verbose_name_plural = _('Сообщения триггеры')

    def __str__(self) -> str:
        return (self.text or 'NULL')[:128]


def _generate_webhook_token() -> str:
    return secrets.token_urlsafe(32)


class TriggerWebhook(models.Model):
    trigger = models.OneToOneField(
        'Trigger',
        on_delete=models.CASCADE,
        related_name='webhook',
        verbose_name=_('Триггер'),
    )
    token = models.CharField(_('Токен'), max_length=64, default=_generate_webhook_token)

    is_authenticated = True  # Stub for IsAuthenticated permission

    class Meta(TypedModelMeta):
        db_table = 'telegram_bot_trigger_webhook'
        verbose_name = _('Webhook триггер')
        verbose_name_plural = _('Webhook триггеры')

    def __str__(self) -> str:
        return str(self.id)

class Trigger(AbstractBlock):
    telegram_bot = models.ForeignKey(
        'TelegramBot',
        on_delete=models.CASCADE,
        related_name='triggers',
        verbose_name=_('Telegram бот'),
    )

    if TYPE_CHECKING:
        command: TriggerCommand
        message: TriggerMessage
        webhook: TriggerWebhook

    class Meta(TypedModelMeta):
        db_table = 'telegram_bot_trigger'
        verbose_name = _('Триггер')
        verbose_name_plural = _('Триггеры')

    def __str__(self) -> str:
        return self.name
