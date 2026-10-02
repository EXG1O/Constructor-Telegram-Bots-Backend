from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from django_stubs_ext.db.models import TypedModelMeta

from telegram_bots.enums import BackgroundTaskStatus

from .base import AbstractBlock


class BackgroundTask(AbstractBlock):
    telegram_bot = models.ForeignKey(
        'TelegramBot',
        on_delete=models.CASCADE,
        related_name='background_tasks',
        verbose_name=_('Telegram бот'),
    )
    status = models.CharField(
        _('Статус'),
        max_length=7,
        choices=BackgroundTaskStatus,
        default=BackgroundTaskStatus.PENDING,
    )
    interval = models.PositiveIntegerField(
        _('Интервал'),
        validators=[
            MinValueValidator(settings.TELEGRAM_BOT_MIN_BACKGROUND_TASK_INTERVAL),
            MaxValueValidator(settings.TELEGRAM_BOT_MAX_BACKGROUND_TASK_INTERVAL),
        ],
    )
    target_connections = None

    class Meta(TypedModelMeta):
        db_table = 'telegram_bot_background_task'
        verbose_name = _('Фоновая задача')
        verbose_name_plural = _('Фоновые задачи')

    def __str__(self) -> str:
        return self.name
