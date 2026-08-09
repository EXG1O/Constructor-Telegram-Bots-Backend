from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from django_stubs_ext.db.models import TypedModelMeta

from .base import AbstractBlock


class Timer(AbstractBlock):
    telegram_bot = models.ForeignKey(
        'TelegramBot',
        on_delete=models.CASCADE,
        related_name='timers',
        verbose_name=_('Telegram бот'),
    )
    duration_seconds = models.PositiveSmallIntegerField(
        _('Длительность в секундах'),
        validators=[MinValueValidator(1), MaxValueValidator(3600)],
    )

    class Meta(TypedModelMeta):
        db_table = 'telegram_bot_timer'
        verbose_name = _('Таймер')
        verbose_name_plural = _('Таймеры')

    def __str__(self) -> str:
        return self.name
