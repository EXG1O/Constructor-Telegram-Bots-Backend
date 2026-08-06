from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import UploadedFile
from django.db import transaction
from django.db.models import QuerySet
from django.db.models.fields.files import FieldFile
from django.utils.translation import gettext as _

from rest_framework import serializers

from constructor_telegram_bots.utils.serializers import (
    validate_exclusive_fields,
    validate_max_count,
)
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
from ..utils.storage import get_media_file_names_queryset
from .base import BlockSerializer, DiagramSerializer, MessageMediaSerializer
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


class MessageSerializer(TelegramBotMixin, BlockSerializer[Message]):
    settings = MessageSettingsSerializer()
    images = MessageImageSerializer(many=True, required=False, allow_null=True)
    documents = MessageDocumentSerializer(many=True, required=False, allow_null=True)
    keyboard = MessageKeyboardSerializer(required=False, allow_null=True)

    class Meta(BlockSerializer.Meta):
        model = Message
        fields = BlockSerializer.Meta.fields + [
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

            validate_exclusive_fields({'file': has_file, 'from_url': has_from_url})

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

        validate_max_count(
            (
                (
                    self.instance.keyboard.buttons.count()
                    + sum('id' not in button_data for button_data in buttons_data)
                )
                if self.instance and self.partial
                else len(buttons_data)
            ),
            settings.TELEGRAM_BOT_MAX_MESSAGE_KEYBOARD_BUTTONS,
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
                    'Необходимо указать значение как минимум для одного из полей: '
                    "'text', 'images', 'documents', 'keyboard'."
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

        images: list[dict[str, Any]] = data.get('images', [])
        documents: list[dict[str, Any]] = data.get('documents', [])
        media: list[dict[str, Any]] = images + documents

        if media:
            new_media_size: int = sum(
                file.size or 0
                for item in media
                if (file := item.get('file')) and isinstance(file, UploadedFile)
            )

            if self.instance:
                image_queryset: QuerySet[MessageImage, str] = (
                    get_media_file_names_queryset(MessageImage, message=self.instance)
                )
                document_queryset: QuerySet[MessageDocument, str] = (
                    get_media_file_names_queryset(
                        MessageDocument, message=self.instance
                    )
                )

                if self.partial:

                    def _extract_media_ids(
                        media: list[dict[str, Any]],
                    ) -> list[int]:
                        return [
                            id
                            for item in media
                            if (id := item.get('id')) and 'file' in item
                        ]

                    image_queryset = image_queryset.filter(
                        id__in=_extract_media_ids(images)
                    )
                    document_queryset = document_queryset.filter(
                        id__in=_extract_media_ids(documents)
                    )

                new_media_size -= sum(
                    map(force_get_file_size, image_queryset.union(document_queryset))
                )

            if (
                new_media_size
                and self.telegram_bot.remaining_storage_size - new_media_size < 0
            ):
                raise serializers.ValidationError(
                    _('Превышен лимит хранилища.'), code='max_storage_size_limit'
                )

        if not self.instance:
            validate_max_count(
                self.telegram_bot.messages.count() + 1,
                settings.TELEGRAM_BOT_MAX_MESSAGES,
            )

        return data

    def create_settings(
        self, message: Message, data: dict[str, Any]
    ) -> MessageSettings:
        return MessageSettings.objects.create(message=message, **data)

    def _create_media[T: AbstractMessageMedia](
        self, message: Message, media_model: type[T], data: list[dict[str, Any]]
    ) -> list[T]:
        create_media: list[T] = []

        for item in data:
            item.pop('id', None)
            create_media.append(media_model(message=message, **item))

        return media_model.objects.bulk_create(create_media)  # type: ignore [attr-defined]

    def create_images(
        self, message: Message, data: list[dict[str, Any]]
    ) -> list[MessageImage]:
        return self._create_media(message, MessageImage, data)

    def create_documents(
        self, message: Message, data: list[dict[str, Any]]
    ) -> list[MessageDocument]:
        return self._create_media(message, MessageDocument, data)

    def create_keyboard(
        self, message: Message, data: dict[str, Any]
    ) -> MessageKeyboard | None:
        buttons_data: list[dict[str, Any]] | None = data.pop('buttons', None)

        if not buttons_data:
            return None

        keyboard: MessageKeyboard = MessageKeyboard.objects.create(
            message=message, **data
        )

        create_buttons: list[MessageKeyboardButton] = []

        for button_data in buttons_data:
            button_data.pop('id', None)
            create_buttons.append(
                MessageKeyboardButton(keyboard=keyboard, **button_data)
            )

        MessageKeyboardButton.objects.bulk_create(create_buttons)

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

    def _update_media[T: AbstractMessageMedia](
        self,
        message: Message,
        media_model: type[T],
        data: list[dict[str, Any]] | None,
    ) -> list[T] | None:
        queryset: QuerySet[T] = getattr(message, media_model.related_name)

        if TYPE_CHECKING:
            file_names: set[str]

        if not data:
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

        create_media: list[T] = []
        update_media: list[T] = []

        delete_file_names: set[str] = set()

        for item in data:
            try:
                media: T = queryset.get(id=item.pop('id'))
            except KeyError, media_model.DoesNotExist:
                create_media.append(media_model(message=message, **item))
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

        new_media: list[T] = media_model.objects.bulk_create(create_media)  # type: ignore [attr-defined]
        media_model.objects.bulk_update(  # type: ignore [attr-defined]
            update_media, fields=['file', 'from_url', 'position']
        )

        if delete_file_names:
            transaction.on_commit(
                functools.partial(self._delete_media_files, delete_file_names)
            )

        final_media: list[T] = new_media + update_media

        if not self.partial:
            new_queryset: QuerySet[T] = queryset.exclude(
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
        return self._update_media(message, MessageImage, data)

    def update_documents(
        self, message: Message, data: list[dict[str, Any]] | None
    ) -> list[MessageDocument] | None:
        return self._update_media(message, MessageDocument, data)

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

        buttons_data: list[dict[str, Any]] = data.get('buttons', [])

        for button_data in buttons_data:
            try:
                button: MessageKeyboardButton = keyboard.buttons.get(
                    id=button_data.pop('id')
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

    def update(self, message: Message, validated_data: dict[str, Any]) -> Message:  # type: ignore[override]
        settings_data: dict[str, Any] | None = validated_data.get('settings')
        images_data: list[dict[str, Any]] | None = validated_data.get('images')
        documents_data: list[dict[str, Any]] | None = validated_data.get('documents')
        keyboard_data: dict[str, Any] | None = validated_data.get('keyboard')

        media: list[AbstractMessageMedia] = []

        try:
            with transaction.atomic():
                super().update(message, validated_data, save=False)
                message.text = validated_data.get('text', message.text)
                message.save(update_fields={*self._UPDATE_FIELDS, 'text'})

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
