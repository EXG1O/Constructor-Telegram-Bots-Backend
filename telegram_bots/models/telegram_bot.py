from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

from django_stubs_ext.db.models import TypedModelMeta

from constructor_telegram_bots.utils.storage import force_get_file_size

from .. import tasks
from ..hub.utils import get_telegram_bots_hub_modal
from .api_request import APIRequest
from .background_task import BackgroundTask
from .condition import Condition
from .connection import Connection
from .database_operation import DatabaseOperation
from .database_record import DatabaseRecord
from .invoice import Invoice, InvoiceImage
from .message import Message, MessageDocument, MessageImage
from .temporary_variable import TemporaryVariable
from .trigger import Trigger
from .user import User
from .variable import Variable

from requests import Response
import requests

from typing import TYPE_CHECKING
import re

TELEGRAM_BOT_TOKEN_PATTERN: re.Pattern[str] = re.compile(r'^\d+:.+$')


def validate_api_token(api_token: str) -> None:
    if (
        not TELEGRAM_BOT_TOKEN_PATTERN.fullmatch(api_token)
        or not requests.get(f'https://api.telegram.org/bot{api_token}/getMe').ok
    ):
        raise ValidationError(_('Этот API-токен является недействительным.'))


class TelegramBot(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='telegram_bots',
        verbose_name=_('Владелец'),
    )
    username = models.CharField('@username', max_length=32)
    api_token = models.CharField(
        _('API-токен'),
        max_length=64,
        unique=True,
        validators=[validate_api_token],
        error_messages={
            'unique': _('Telegram бот с таким API-токеном уже существует.')
        },
    )
    storage_size = models.PositiveBigIntegerField(
        _('Размер хранилища'), default=41943040
    )
    is_private = models.BooleanField(_('Приватный'), default=False)
    must_be_enabled = models.BooleanField(_('Должен быть включен'), default=False)
    is_loading = models.BooleanField(_('Загружается'), default=False)
    added_date = models.DateTimeField(_('Добавлен'), auto_now_add=True)

    hub = models.ForeignKey(
        'telegram_bots_hub.TelegramBotsHub',
        on_delete=models.SET_NULL,
        related_name='bots',
        verbose_name=_('Хаб'),
        blank=True,
        null=True,
    )

    if TYPE_CHECKING:
        connections: models.Manager[Connection]
        triggers: models.Manager[Trigger]
        messages: models.Manager[Message]
        conditions: models.Manager[Condition]
        background_tasks: models.Manager[BackgroundTask]
        api_requests: models.Manager[APIRequest]
        database_operations: models.Manager[DatabaseOperation]
        invoices: models.Manager[Invoice]
        temporary_variables: models.Manager[TemporaryVariable]
        variables: models.Manager[Variable]
        users: models.Manager[User]
        database_records: models.Manager[DatabaseRecord]

    class Meta(TypedModelMeta):
        db_table = 'telegram_bot'
        verbose_name = _('Telegram бота')
        verbose_name_plural = _('Telegram боты')

    def __str__(self) -> str:
        return f'@{self.username}'

    @cached_property
    def used_storage_size(self) -> int:
        """The property is cached, because it make heavy query to database."""

        return sum(
            map(
                force_get_file_size,  # type: ignore [arg-type]
                MessageImage.objects.exclude(file='')
                .filter(message__telegram_bot=self)
                .values_list('file', flat=True)
                .union(
                    MessageDocument.objects.exclude(file='')
                    .filter(message__telegram_bot=self)
                    .values_list('file', flat=True),
                    InvoiceImage.objects.exclude(file='')
                    .filter(invoice__telegram_bot=self)
                    .values_list('file', flat=True),
                ),
            )
        )

    @property
    def remaining_storage_size(self) -> int:
        return self.storage_size - self.used_storage_size

    @property
    def webhook_url(self) -> str:
        return str(
            settings.SELF_URL
            / reverse('api:webhooks:telegram', kwargs={'bot_id': self.id}).removeprefix(
                '/'
            )
        )

    @property
    def is_enabled(self) -> bool:
        try:
            return bool(self.must_be_enabled and self.hub)
        except get_telegram_bots_hub_modal().DoesNotExist:
            return False

    def update_username(self, save: bool = True) -> None:
        response: Response = requests.get(
            f'https://api.telegram.org/bot{self.api_token}/getMe'
        )
        response.raise_for_status()

        self.username = response.json()['result']['username']

        if save:
            self.save(update_fields=['username'])

    def start(self, save: bool = True) -> None:
        self.must_be_enabled = True
        self.is_loading = True

        if save:
            self.save(update_fields=['must_be_enabled', 'is_loading'])

        tasks.start_telegram_bot.delay(
            id=self.id, token=self.api_token, webhook_url=self.webhook_url
        )

    def restart(self, save: bool = True) -> None:
        self.is_loading = True

        if save:
            self.save(update_fields=['is_loading'])

        tasks.restart_telegram_bot.delay(
            id=self.id, token=self.api_token, webhook_url=self.webhook_url
        )

    def stop(self, save: bool = True) -> None:
        self.must_be_enabled = False
        self.is_loading = True

        if save:
            self.save(update_fields=['must_be_enabled', 'is_loading'])

        tasks.stop_telegram_bot.delay(id=self.id)
