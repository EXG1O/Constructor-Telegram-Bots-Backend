from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils.translation import gettext_lazy as _

from django_stubs_ext.db.models import TypedModelMeta

from premium.models import Subscription, SubscriptionInvoice
from telegram_bots.models import TelegramBot

from .enums import TokenType

from typing import TYPE_CHECKING, Any


class UserManager(BaseUserManager['User']):
    def create_superuser(self, **fields: Any) -> User:
        return self.create(is_staff=True, is_superuser=True, **fields)


class User(AbstractBaseUser, PermissionsMixin):
    password = None  # type: ignore [assignment]

    telegram_id = models.PositiveBigIntegerField('Telegram ID', unique=True)
    first_name = models.CharField(_('Имя'), max_length=64)
    last_name = models.CharField(_('Фамилия'), max_length=64, null=True)
    accepted_terms = models.BooleanField(_('Принятие условий сервиса'), default=False)
    terms_accepted_date = models.DateTimeField(
        _('Дата принятия условий сервиса'), null=True, blank=True
    )
    is_staff = models.BooleanField(_('Сотрудник'), default=False)
    joined_date = models.DateTimeField(_('Присоединился'), auto_now_add=True)

    if TYPE_CHECKING:
        tokens: models.Manager[Token]
        subscription_invoices: models.Manager[SubscriptionInvoice]
        subscription: Subscription
        telegram_bots: models.Manager[TelegramBot]

    USERNAME_FIELD = 'telegram_id'

    objects = UserManager()

    class Meta(TypedModelMeta):
        db_table = 'user'
        verbose_name = _('Пользователя')
        verbose_name_plural = _('Пользователи')

    def __str__(self) -> str:
        return f'Telegram ID: {self.telegram_id}'

    @property
    def full_name(self) -> str:
        return f'{self.first_name} {self.last_name or ""}'.strip()

    @property
    def has_subscription(self) -> bool:
        try:
            return bool(self.subscription and not self.subscription.is_expired)
        except Subscription.DoesNotExist:
            return False


class Token(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name='tokens',
        verbose_name=_('Пользователь'),
        blank=True,
        null=True,
    )
    jti = models.CharField('JWT ID', primary_key=True, max_length=32)
    type = models.CharField(_('Тип'), max_length=7, choices=TokenType)
    expiry_date = models.DateTimeField(_('Срок действия'))
    created_date = models.DateTimeField(_('Создан'), auto_now_add=True)

    if TYPE_CHECKING:
        blacklisted: BlacklistedToken

    class Meta(TypedModelMeta):
        db_table = 'user_token'
        verbose_name = _('Токен')
        verbose_name_plural = _('Токены')

    def __str__(self) -> str:
        return self.jti


class BlacklistedToken(models.Model):
    token = models.OneToOneField(
        Token,
        on_delete=models.CASCADE,
        related_name='blacklisted',
        verbose_name=_('Токен'),
    )
    blacklisted_date = models.DateTimeField(_('Внесён'), auto_now_add=True)

    class Meta(TypedModelMeta):
        db_table = 'user_blacklisted_token'
        verbose_name = _('Токен в чёрном списке')
        verbose_name_plural = _('Токены в чёрном списке')

    def __str__(self) -> str:
        return self.token.jti
