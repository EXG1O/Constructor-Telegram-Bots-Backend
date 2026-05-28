from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import UploadedFile
from django.db import transaction
from django.db.models import QuerySet
from django.db.models.fields.files import FieldFile
from django.utils.translation import gettext as _

from rest_framework import serializers

from constructor_telegram_bots.utils.storage import force_get_file_size

from ..models import (
    Message,
    MessageDocument,
    MessageImage,
    MessageKeyboard,
    MessageKeyboardButton,
    MessageSettings,
)
from ..models.base import AbstractMessageMedia
from .base import AMMT, DiagramSerializer, MessageMediaSerializer
from .connection import ConnectionSerializer
from .mixins import TelegramBotMixin

from collections.abc import Iterable
from contextlib import suppress
from typing import TYPE_CHECKING, Any, cast
import functools


class MessageSettingsSerializer(serializers.ModelSerializer[MessageSettings]):
    class Meta:
        model = MessageSettings
        fields = ['reply_to_user_message', 'delete_user_message', 'send_as_new_message']


class MessageImageSerializer(MessageMediaSerializer[MessageImage]):
    class Meta(MessageMediaSerializer.Meta):
        model = MessageImage


class MessageDocumentSerializer(MessageMediaSerializer[MessageDocument]):
    class Meta(MessageMediaSerializer.Meta):
        model = MessageDocument


class MessageKeyboardButtonSerializer(
    serializers.ModelSerializer[MessageKeyboardButton]
):
    class Meta:
        model = MessageKeyboardButton
        fields = ['id', 'row', 'position', 'text', 'url', 'style']
        extra_kwargs = {'id': {'read_only': False, 'required': False}}


class MessageKeyboardSerializer(serializers.ModelSerializer[MessageKeyboard]):
    buttons = MessageKeyboardButtonSerializer(many=True)

    class Meta:
        model = MessageKeyboard
        fields = ['type', 'buttons']


class MessageSerializer(TelegramBotMixin, serializers.ModelSerializer[Message]):
    settings = MessageSettingsSerializer()
    images = MessageImageSerializer(many=True, required=False, allow_null=True)
    documents = MessageDocumentSerializer(many=True, required=False, allow_null=True)
    keyboard = MessageKeyboardSerializer(required=False, allow_null=True)

    class Meta:
        model = Message
        fields = [
            'id',
            'name',
            'text',
            'settings',
            'images',
            'documents',
            'keyboard',
        ]

    def _validate_media(
        self,
        media_model_class: type[AbstractMessageMedia],
        media_data: list[dict[str, Any]] | None,
    ) -> list[dict[str, Any]] | None:
        if not media_data:
            return media_data

        queryset: QuerySet[AbstractMessageMedia] | None = None

        if self.instance and self.partial:
            queryset = getattr(self.instance, media_model_class.related_name)

        for item in media_data:
            has_file: bool = bool(item.get('file'))
            has_from_url: bool = bool(item.get('from_url'))

            if queryset:
                with suppress(KeyError, media_model_class.DoesNotExist):
                    media: AbstractMessageMedia = queryset.get(id=item['id'])  # type: ignore [misc]

                    if not has_file:
                        has_file = bool(media.file)
                    if not has_from_url:
                        has_from_url = bool(media.from_url)

            if has_file is has_from_url:
                raise serializers.ValidationError(
                    'Медиа должен иметь значение только для одного из полей: '
                    "'file' или 'from_url'."
                )

        return media_data

    def validate_images(
        self, data: list[dict[str, Any]] | None
    ) -> list[dict[str, Any]] | None:
        return self._validate_media(MessageImage, data)

    def validate_documents(
        self, data: list[dict[str, Any]] | None
    ) -> list[dict[str, Any]] | None:
        return self._validate_media(MessageDocument, data)

    def validate_keyboard(self, data: dict[str, Any] | None) -> dict[str, Any] | None:
        if not data:
            return None

        buttons_data: list[dict[str, Any]] | None = data.get('buttons')

        if not buttons_data:
            return None

        if (
            self.instance.keyboard.buttons.count()
            + sum('id' not in button_data for button_data in buttons_data)
            if self.instance and self.partial
            else len(buttons_data)
        ) > settings.TELEGRAM_BOT_MAX_MESSAGE_KEYBOARD_BUTTONS:
            raise serializers.ValidationError(
                _('Нельзя добавлять больше %(max)s кнопок для клавиатуры сообщения.')
                % {'max': settings.TELEGRAM_BOT_MAX_MESSAGE_KEYBOARD_BUTTONS},
                code='max_limit',
            )

        return data

    def validate(self, data: dict[str, Any]) -> dict[str, Any]:
        has_text: bool = bool(
            data.get('text', self.instance.text if self.instance else None)
        )
        has_images: bool = bool(
            data.get('images', self.instance.images.count() if self.instance else None)
        )
        has_documents: bool = bool(
            data.get(
                'documents', self.instance.documents.count() if self.instance else None
            )
        )
        has_keyboard: bool = bool(data.get('keyboard'))

        if self.instance and not has_keyboard:
            with suppress(MessageKeyboard.DoesNotExist):
                has_keyboard = bool(self.instance.keyboard)

        if not any([has_text, has_images, has_documents, has_keyboard]):
            raise serializers.ValidationError(
                _(
                    "Необходимо указать значение минимум для одно из полей: 'text', "
                    "'images', 'documents' или 'keyboard'."
                ),
                code='required',
            )

        if has_keyboard and not has_text:
            raise serializers.ValidationError(
                _(
                    "Необходимо указать значение для поле 'text', если указано значение "
                    "для поля 'keyboard'."
                ),
                code='required',
            )

        images: list[dict[str, Any]] | None = data.get('images')
        documents: list[dict[str, Any]] | None = data.get('documents')

        if images or documents:
            new_media_size: int = sum(
                file.size or 0
                for media in (images or []) + (documents or [])
                if (file := media.get('file')) and isinstance(file, UploadedFile)
            )

            if self.instance and not self.partial:
                existing_media_size: int = sum(
                    map(
                        force_get_file_size,  # type: ignore [arg-type]
                        MessageImage.objects.exclude(file='')
                        .filter(message=self.instance)
                        .values_list('file', flat=True)
                        .union(
                            MessageDocument.objects.exclude(file='')
                            .filter(message=self.instance)
                            .values_list('file', flat=True)
                        ),
                    )
                )
                new_media_size -= existing_media_size

            if (
                new_media_size
                and self.telegram_bot.remaining_storage_size - new_media_size < 0
            ):
                raise serializers.ValidationError(
                    _('Превышен лимит хранилища.'), code='max_storage_size_limit'
                )

        if (
            not self.instance
            and self.telegram_bot.messages.count() + 1
            > settings.TELEGRAM_BOT_MAX_MESSAGES
        ):
            raise serializers.ValidationError(
                _('Нельзя добавлять больше %(max)s сообщений.')
                % {'max': settings.TELEGRAM_BOT_MAX_MESSAGES},
                code='max_limit',
            )

        return data

    def create_settings(
        self, message: Message, data: dict[str, Any]
    ) -> MessageSettings:
        return MessageSettings.objects.create(message=message, **data)

    def create_images(
        self, message: Message, data: list[dict[str, Any]]
    ) -> list[MessageImage]:
        return MessageImage.objects.bulk_create(
            MessageImage(message=message, **item) for item in data
        )

    def create_documents(
        self, message: Message, data: list[dict[str, Any]]
    ) -> list[MessageDocument]:
        return MessageDocument.objects.bulk_create(
            MessageDocument(message=message, **item) for item in data
        )

    def create_keyboard(
        self, message: Message, data: dict[str, Any]
    ) -> MessageKeyboard | None:
        buttons_data: list[dict[str, Any]] | None = data.pop('buttons', None)

        if not buttons_data:
            return None

        keyboard: MessageKeyboard = MessageKeyboard.objects.create(
            message=message, **data
        )
        MessageKeyboardButton.objects.bulk_create(
            MessageKeyboardButton(keyboard=keyboard, **button_data)
            for button_data in buttons_data
        )

        return keyboard

    def create(self, validated_data: dict[str, Any]) -> Message:
        settings_data: dict[str, Any] = validated_data.pop('settings')
        images_data: list[dict[str, Any]] | None = validated_data.pop('images', None)
        documents_data: list[dict[str, Any]] | None = validated_data.pop(
            'documents', None
        )
        keyboard_data: dict[str, Any] | None = validated_data.pop('keyboard', None)

        media: list[AbstractMessageMedia] = []

        try:
            with transaction.atomic():
                message: Message = self.telegram_bot.messages.create(**validated_data)

                self.create_settings(message, settings_data)
                if images_data:
                    media += self.create_images(message, images_data)
                if documents_data:
                    media += self.create_documents(message, documents_data)
                if keyboard_data:
                    self.create_keyboard(message, keyboard_data)
        except Exception as error:
            for item in media:
                if (file := item.file) and (file_name := file.name):
                    default_storage.delete(file_name)
            raise error

        return message

    def update_settings(
        self, message: Message, data: dict[str, Any] | None
    ) -> MessageSettings | None:
        if not data:
            return None

        settings: MessageSettings = message.settings
        settings.reply_to_user_message = data.get(
            'reply_to_user_message', settings.reply_to_user_message
        )
        settings.delete_user_message = data.get(
            'delete_user_message', settings.delete_user_message
        )
        settings.send_as_new_message = data.get(
            'send_as_new_message', settings.send_as_new_message
        )
        settings.save(
            update_fields=[
                'reply_to_user_message',
                'delete_user_message',
                'send_as_new_message',
            ]
        )

        return settings

    def _delete_media_files(self, file_names: Iterable[str]) -> None:
        for file_name in file_names:
            default_storage.delete(file_name)

    def update_media(
        self,
        message: Message,
        media_model_class: type[AMMT],
        media_data: list[dict[str, Any]] | None,
    ) -> list[AMMT] | None:
        queryset: QuerySet[AMMT] = getattr(message, media_model_class.related_name)

        if TYPE_CHECKING:
            file_names: set[str]

        if not media_data:
            if not self.partial:
                file_names = set(
                    queryset.exclude(file=None).values_list('file', flat=True)
                )
                queryset.all().delete()

                if file_names:
                    transaction.on_commit(
                        functools.partial(self._delete_media_files, file_names)
                    )
            return None

        create_media: list[AMMT] = []
        update_media: list[AMMT] = []

        delete_file_names: set[str] = set()

        for item in media_data:
            try:
                media: AMMT = queryset.get(id=item['id'])
            except KeyError, media_model_class.DoesNotExist:
                create_media.append(media_model_class(message=message, **item))
            else:
                new_file: UploadedFile | None = item.get('file')
                old_file: FieldFile | None = media.file

                if new_file and new_file.name:
                    media.file = new_file
                    cast(FieldFile, media.file).save(new_file.name, new_file, save=True)
                else:
                    media.file = None

                media.from_url = item.get('from_url', media.from_url)
                media.position = item.get('position', media.position)
                update_media.append(media)

                if old_file and (file_name := old_file.name):
                    delete_file_names.add(file_name)

        new_media: list[AMMT] = media_model_class.objects.bulk_create(create_media)  # type: ignore [attr-defined]
        media_model_class.objects.bulk_update(  # type: ignore [attr-defined]
            update_media, fields=['file', 'from_url', 'position']
        )

        if delete_file_names:
            transaction.on_commit(
                functools.partial(self._delete_media_files, delete_file_names)
            )

        final_media: list[AMMT] = new_media + update_media

        if not self.partial:
            new_queryset: QuerySet[AMMT] = queryset.exclude(
                id__in=[media.id for media in final_media]  # type: ignore [attr-defined]
            )
            file_names = set(
                new_queryset.exclude(file=None).values_list('file', flat=True)
            )
            new_queryset.delete()

            if file_names:
                transaction.on_commit(
                    functools.partial(self._delete_media_files, file_names)
                )

        return final_media

    def update_images(
        self, message: Message, data: list[dict[str, Any]] | None
    ) -> list[MessageImage] | None:
        return self.update_media(message, MessageImage, data)

    def update_documents(
        self, message: Message, data: list[dict[str, Any]] | None
    ) -> list[MessageDocument] | None:
        return self.update_media(message, MessageDocument, data)

    def update_keyboard(
        self, message: Message, data: dict[str, Any] | None
    ) -> MessageKeyboard | None:
        if not data:
            if not self.partial:
                with suppress(MessageKeyboard.DoesNotExist):
                    message.keyboard.delete()
                    del message._state.fields_cache['keyboard']
            return None

        try:
            keyboard: MessageKeyboard = message.keyboard
        except MessageKeyboard.DoesNotExist:
            return self.create_keyboard(message, data)

        keyboard_type: str = data.get('type', keyboard.type)

        keyboard.type = keyboard_type
        keyboard.save(update_fields=['type'])

        create_buttons: list[MessageKeyboardButton] = []
        update_buttons: list[MessageKeyboardButton] = []

        for button_data in data.get('buttons', []):
            try:
                button: MessageKeyboardButton = keyboard.buttons.get(
                    id=button_data['id']
                )
            except KeyError, MessageKeyboardButton.DoesNotExist:
                if keyboard_type != 'default':
                    button_data['url'] = None

                create_buttons.append(
                    MessageKeyboardButton(keyboard=keyboard, **button_data)
                )
            else:
                button.row = button_data.get('row', button.row)
                button.position = button_data.get('position', button.position)
                button.text = button_data.get('text', button.text)
                button.url = (
                    button_data.get('url', button.url)
                    if keyboard_type != 'default'
                    else None
                )
                button.style = button_data.get('style', button.style)
                update_buttons.append(button)

        new_buttons: list[MessageKeyboardButton] = (
            MessageKeyboardButton.objects.bulk_create(create_buttons)
        )
        MessageKeyboardButton.objects.bulk_update(
            update_buttons, fields=['row', 'position', 'text', 'url', 'style']
        )

        if not self.partial:
            keyboard.buttons.exclude(
                id__in=[button.id for button in new_buttons + update_buttons]
            ).delete()

        return keyboard

    def update(self, message: Message, validated_data: dict[str, Any]) -> Message:
        settings_data: dict[str, Any] | None = validated_data.get('settings')
        images_data: list[dict[str, Any]] | None = validated_data.get('images')
        documents_data: list[dict[str, Any]] | None = validated_data.get('documents')
        keyboard_data: dict[str, Any] | None = validated_data.get('keyboard')

        media: list[AbstractMessageMedia] = []

        try:
            with transaction.atomic():
                message.name = validated_data.get('name', message.name)
                message.text = validated_data.get('text', message.text)
                message.save(update_fields=['name', 'text'])

                self.update_settings(message, settings_data)
                media += self.update_images(message, images_data) or []
                media += self.update_documents(message, documents_data) or []
                self.update_keyboard(message, keyboard_data)
        except Exception as error:
            for item in media:
                if (file := item.file) and (file_name := file.name):
                    default_storage.delete(file_name)
            raise error

        return message


class DiagramMessageKeyboardButtonSerializer(
    serializers.ModelSerializer[MessageKeyboardButton]
):
    source_connections = ConnectionSerializer(many=True)

    class Meta:
        model = MessageKeyboardButton
        fields = ['id', 'row', 'position', 'text', 'url', 'style', 'source_connections']


class DiagramMessageKeyboardSerializer(serializers.ModelSerializer[MessageKeyboard]):
    buttons = DiagramMessageKeyboardButtonSerializer(many=True)

    class Meta:
        model = MessageKeyboard
        fields = ['type', 'buttons']


class DiagramMessageSerializer(DiagramSerializer[Message]):
    keyboard = DiagramMessageKeyboardSerializer(allow_null=True, read_only=True)
    source_connections = ConnectionSerializer(many=True, read_only=True)

    class Meta(DiagramSerializer.Meta):
        model = Message
        fields = DiagramSerializer.Meta.fields + ['text', 'keyboard']
        read_only_fields = DiagramSerializer.Meta.read_only_fields + ['text']
