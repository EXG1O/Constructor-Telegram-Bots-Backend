from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.utils.translation import gettext_lazy as _

from django_stubs_ext.db.models import TypedModelMeta

from constructor_telegram_bots.fields import PublicURLField

from ..enums import KeyboardButtonStyle, KeyboardType
from .base import AbstractBlock, AbstractMessageMedia, upload_media_path

from typing import TYPE_CHECKING


class MessageSettings(models.Model):
    message = models.OneToOneField(
        'Message',
        on_delete=models.CASCADE,
        related_name='settings',
        verbose_name=_('Сообщение'),
    )
    reply_to_user_message = models.BooleanField(
        _('Ответить на сообщение пользователя'), default=False
    )
    delete_user_message = models.BooleanField(
        _('Удалить сообщение пользователя'), default=False
    )
    send_as_new_message = models.BooleanField(
        _('Отправить сообщение как новое'), default=True
    )

    class Meta(TypedModelMeta):
        db_table = 'telegram_bot_message_settings'
        verbose_name = _('Настройки сообщения')
        verbose_name_plural = _('Настройки сообщений')

    def __str__(self) -> str:
        return self.message.name


class MessageImage(AbstractMessageMedia):
    related_name = 'images'

    message = models.ForeignKey(
        'Message',
        on_delete=models.CASCADE,
        related_name=related_name,
        verbose_name=_('Сообщение'),
    )
    file = models.ImageField(
        _('Изображение'),
        upload_to=upload_media_path,
        max_length=500,
        blank=True,
        null=True,
    )

    class Meta(TypedModelMeta):
        db_table = 'telegram_bot_message_image'
        verbose_name = _('Изображение сообщения')
        verbose_name_plural = _('Изображения сообщений')

    def __str__(self) -> str:
        return self.message.name


class MessageDocument(AbstractMessageMedia):
    related_name = 'documents'

    message = models.ForeignKey(
        'Message',
        on_delete=models.CASCADE,
        related_name=related_name,
        verbose_name=_('Сообщение'),
    )
    file = models.FileField(
        _('Документ'),
        upload_to=upload_media_path,
        max_length=500,
        blank=True,
        null=True,
    )

    class Meta(TypedModelMeta):
        db_table = 'telegram_bot_message_document'
        verbose_name = _('Документ сообщения')
        verbose_name_plural = _('Документы сообщений')

    def __str__(self) -> str:
        return self.message.name


class MessageKeyboardButton(models.Model):
    keyboard = models.ForeignKey(
        'MessageKeyboard',
        on_delete=models.CASCADE,
        related_name='buttons',
        verbose_name=_('Клавиатура'),
    )
    row = models.PositiveSmallIntegerField(_('Ряд'))
    position = models.PositiveSmallIntegerField(_('Позиция'))
    text = models.TextField(_('Текст'), max_length=512)
    url = PublicURLField(_('URL-адрес'), blank=True, null=True)
    style = models.CharField(
        _('Стиль'),
        max_length=7,
        choices=KeyboardButtonStyle,
        default=KeyboardButtonStyle.DEFAULT,
    )
    source_connections = GenericRelation(
        'Connection', 'source_object_id', 'source_content_type'
    )

    class Meta(TypedModelMeta):
        db_table = 'telegram_bot_message_keyboard_button'
        verbose_name = _('Кнопка клавиатуры сообщения')
        verbose_name_plural = _('Кнопки клавиатур сообщений')
        indexes = [models.Index(fields=['text'])]

    def __str__(self) -> str:
        return self.keyboard.message.name


class MessageKeyboard(models.Model):
    message = models.OneToOneField(
        'Message',
        on_delete=models.CASCADE,
        related_name='keyboard',
        verbose_name=_('Сообщение'),
    )
    type = models.CharField(
        _('Режим'), max_length=7, choices=KeyboardType, default=KeyboardType.DEFAULT
    )

    if TYPE_CHECKING:
        buttons: models.Manager[MessageKeyboardButton]

    class Meta(TypedModelMeta):
        db_table = 'telegram_bot_message_keyboard'
        verbose_name = _('Клавиатура сообщения')
        verbose_name_plural = _('Клавиатуры сообщений')

    def __str__(self) -> str:
        return self.message.name


class Message(AbstractBlock):
    telegram_bot = models.ForeignKey(
        'TelegramBot',
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name=_('Telegram бот'),
    )
    text = models.TextField(_('Текст'), max_length=4096, null=True, default=None)

    if TYPE_CHECKING:
        settings: MessageSettings
        images: models.Manager[MessageImage]
        documents: models.Manager[MessageDocument]
        keyboard: MessageKeyboard

    class Meta(TypedModelMeta):
        db_table = 'telegram_bot_message'
        verbose_name = _('Сообщение')
        verbose_name_plural = _('Сообщения')

    def __str__(self) -> str:
        return self.name
