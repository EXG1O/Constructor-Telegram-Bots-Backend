from django.db import models
from django.utils.translation import gettext_lazy as _

from django_stubs_ext.db.models import TypedModelMeta

from constructor_telegram_bots.fields import StrictJSONField

from .base import AbstractBlock

from typing import TYPE_CHECKING


class DatabaseCreateOperation(models.Model):
    operation = models.OneToOneField(
        'DatabaseOperation',
        on_delete=models.CASCADE,
        related_name='create_operation',
        verbose_name=_('Операция'),
    )
    data = StrictJSONField(_('Данные'), max_length=4096)

    class Meta(TypedModelMeta):
        db_table = 'telegram_bot_database_create_operation'
        verbose_name = _('Операция создания записи')
        verbose_name_plural = _('Операции создания записей')

    def __str__(self) -> str:
        return self.operation.name


class DatabaseUpdateOperation(models.Model):
    operation = models.OneToOneField(
        'DatabaseOperation',
        on_delete=models.CASCADE,
        related_name='update_operation',
        verbose_name=_('Операция'),
    )
    overwrite = models.BooleanField(_('Перезаписать'), default=True)
    lookup_field_name = models.CharField(_('Название поля для поиска'), max_length=255)
    lookup_field_value = models.CharField(_('Значение поля для поиска'), max_length=255)
    create_if_not_found = models.BooleanField(
        _('Создать, если не найдена'), default=True
    )
    new_data = StrictJSONField(_('Новые данные'), max_length=4096)

    class Meta(TypedModelMeta):
        db_table = 'telegram_bot_database_update_operation'
        verbose_name = _('Операция обновления записи')
        verbose_name_plural = _('Операции обновления записей')

    def __str__(self) -> str:
        return self.operation.name


class DatabaseOperation(AbstractBlock):
    telegram_bot = models.ForeignKey(
        'TelegramBot',
        on_delete=models.CASCADE,
        related_name='database_operations',
        verbose_name=_('Telegram бот'),
    )

    if TYPE_CHECKING:
        create_operation: DatabaseCreateOperation
        update_operation: DatabaseUpdateOperation

    class Meta(TypedModelMeta):
        db_table = 'telegram_bot_database_operation'
        verbose_name = _('Операция базы данных')
        verbose_name_plural = _('Операции баз данных')

    def __str__(self) -> str:
        return self.name
