from django.db import models
from django.utils.translation import gettext_lazy as _

from django_stubs_ext.db.models import TypedModelMeta

from .chat import Chat


class User(models.Model):
    telegram_bot = models.ForeignKey(
        'TelegramBot',
        on_delete=models.CASCADE,
        related_name='users',
        verbose_name=_('Telegram бот'),
    )
    telegram_id = models.PositiveBigIntegerField('Telegram ID')
    username = models.CharField(
        _('Имя пользователя'), max_length=32, blank=True, null=True
    )
    first_name = models.CharField(_('Имя'), max_length=64)
    last_name = models.CharField(_('Фамилия'), max_length=64, blank=True, null=True)
    is_bot = models.BooleanField(_('Бот'), default=False)
    is_premium = models.BooleanField(_('Премиум'), default=False)
    is_allowed = models.BooleanField(_('Разрешён'), default=False)
    is_blocked = models.BooleanField(_('Заблокирован'), default=False)
    last_activity_date = models.DateTimeField(
        _('Дата последней активности'), auto_now_add=True
    )
    activated_date = models.DateTimeField(_('Дата активации'), auto_now_add=True)

    chats = models.ManyToManyField(
        Chat, related_name='users', verbose_name=_('Чаты'), blank=True
    )

    class Meta(TypedModelMeta):
        db_table = 'telegram_bot_user'
        indexes = [models.Index(fields=['telegram_id'])]
        verbose_name = _('Пользователя')
        verbose_name_plural = _('Пользователи')

    def __str__(self) -> str:
        return f'{self.first_name} {self.last_name or ""}'.strip()
