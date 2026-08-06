from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import gettext_lazy as _

from django_stubs_ext.db.models import TypedModelMeta

from ..enums import ConnectionHandlePosition


class Connection(models.Model):
    telegram_bot = models.ForeignKey(
        'TelegramBot',
        on_delete=models.CASCADE,
        related_name='connections',
        verbose_name=_('Telegram бот'),
    )

    source_content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE, related_name='source_connections'
    )
    source_object_id = models.PositiveBigIntegerField()
    source_object = GenericForeignKey('source_content_type', 'source_object_id')
    source_handle_position = models.CharField(
        _('Стартовая позиция коннектора'),
        max_length=5,
        choices=ConnectionHandlePosition,
    )

    target_content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE, related_name='target_connections'
    )
    target_object_id = models.PositiveBigIntegerField()
    target_object = GenericForeignKey('target_content_type', 'target_object_id')
    target_handle_position = models.CharField(
        _('Окончательная позиция коннектора'),
        max_length=5,
        choices=ConnectionHandlePosition,
    )

    class Meta(TypedModelMeta):
        db_table = 'telegram_bot_block_connection'
        verbose_name = _('Подключение')
        verbose_name_plural = _('Подключения')
        indexes = [
            models.Index(fields=['source_content_type', 'source_object_id']),
            models.Index(fields=['target_content_type', 'target_object_id']),
        ]

    def __str__(self) -> str:
        return (
            f'{self.source_content_type}:{self.source_object_id} -> '
            f'{self.target_content_type}:{self.target_object_id}'
        )
