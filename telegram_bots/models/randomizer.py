from django.db import models
from django.utils.translation import gettext_lazy as _

from django_stubs_ext.db.models import TypedModelMeta

from .base import AbstractBlock


class Randomizer(AbstractBlock):
    telegram_bot = models.ForeignKey(
        'TelegramBot',
        on_delete=models.CASCADE,
        related_name='randomizers',
        verbose_name=_('Telegram бот'),
    )

    class Meta(TypedModelMeta):
        db_table = 'telegram_bot_randomizer'
        verbose_name = _('Рандомайзер')
        verbose_name_plural = _('Рандомайзеры')

    def __str__(self) -> str:
        return self.name
