from django.db import models
from django.utils.translation import gettext_lazy as _

from django_stubs_ext.db.models import TypedModelMeta

from ..enums import ActionMessageDeletionTarget
from .base import AbstractBlock

from typing import TYPE_CHECKING


class ActionMessageDeletion(models.Model):
    action = models.OneToOneField(
        'Action',
        on_delete=models.CASCADE,
        related_name='message_deletion',
        verbose_name=_('Действие'),
    )
    target = models.CharField(
        _('Цель'), max_length=32, choices=ActionMessageDeletionTarget
    )

    class Meta(TypedModelMeta):
        db_table = 'telegram_bot_action_message_deletion'
        verbose_name = _('Действие по удалению сообщения')
        verbose_name_plural = _('Действия по удалению сообщений')

    def __str__(self) -> str:
        return f'ID: {self.id}'


class Action(AbstractBlock):
    telegram_bot = models.ForeignKey(
        'TelegramBot',
        on_delete=models.CASCADE,
        related_name='actions',
        verbose_name=_('Telegram бот'),
    )

    if TYPE_CHECKING:
        message_deletion: ActionMessageDeletion

    class Meta(TypedModelMeta):
        db_table = 'telegram_bot_action'
        verbose_name = _('Действие')
        verbose_name_plural = _('Действия')

    def __str__(self) -> str:
        return self.name
