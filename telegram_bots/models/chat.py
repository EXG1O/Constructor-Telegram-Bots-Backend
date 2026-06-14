from django.db import models
from django.utils.translation import gettext_lazy as _

from django_stubs_ext.db.models import TypedModelMeta

from ..enums import ChatType

from typing import TYPE_CHECKING


class Chat(models.Model):
    telegram_bot = models.ForeignKey(
        'TelegramBot',
        on_delete=models.CASCADE,
        related_name='chats',
        verbose_name=_('Telegram бот'),
    )
    telegram_id = models.BigIntegerField('Telegram ID')
    type = models.CharField(
        _('Тип'),
        max_length=16,
        choices=ChatType.choices,
    )
    title = models.CharField(_('Название'), max_length=255, blank=True, null=True)
    username = models.CharField('@username', max_length=32, blank=True, null=True)
    first_name = models.CharField(_('Имя'), max_length=64, blank=True, null=True)
    last_name = models.CharField(_('Фамилия'), max_length=64, blank=True, null=True)
    is_forum = models.BooleanField(_('Форум'), default=False)
    is_direct_messages = models.BooleanField(_('Прямые сообщения'), default=False)
    is_allowed = models.BooleanField(_('Разрешён'), default=False)
    is_blocked = models.BooleanField(_('Заблокирован'), default=False)

    if TYPE_CHECKING:
        from django.db.models.fields.related_descriptors import ManyRelatedManager

        from .user import User

        users: ManyRelatedManager[User]

    class Meta(TypedModelMeta):
        db_table = 'telegram_bot_chat'
        indexes = [models.Index(fields=['telegram_id'])]
        verbose_name = _('Чат')
        verbose_name_plural = _('Чаты')

    def __str__(self) -> str:
        return (
            self.title
            or f'{self.first_name or ""} {self.last_name or ""}'.strip()
            or str(self.telegram_id)
        )
