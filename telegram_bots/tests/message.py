from django.conf import settings
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory, force_authenticate

from constructor_telegram_bots.utils.tests import assert_view_basic_protected
from users.tests.mixins import UserMixin
from users.utils.tests import assert_view_requires_terms_acceptance

from ..enums import KeyboardType
from ..models import Message, MessageKeyboard
from ..views import DiagramMessageViewSet, MessageViewSet
from .mixins import MessageMixin, TelegramBotMixin

from typing import Any


class MessageViewSetTestCase(MessageMixin, TelegramBotMixin, UserMixin, TestCase):
    def setUp(self) -> None:
        super().setUp()

        self.factory = APIRequestFactory()

        self.keyboard: MessageKeyboard = MessageKeyboard.objects.create(
            message=self.message, type=KeyboardType.DEFAULT
        )
        self.keyboard.buttons.create(row=0, position=0, text='Test button text')

        self.list_url_kwargs: dict[str, Any] = {'telegram_bot_id': self.telegram_bot.id}
        self.detail_url_kwargs: dict[str, Any] = {
            **self.list_url_kwargs,
            'id': self.message.id,
        }

        self.list_url: str = reverse(
            'api:telegram-bots:telegram-bot-message-list',
            kwargs=self.list_url_kwargs,
        )
        self.detail_url: str = reverse(
            'api:telegram-bots:telegram-bot-message-detail',
            kwargs=self.detail_url_kwargs,
        )

    def test_invalid_telegram_bot_id(self) -> None:
        view = MessageViewSet.as_view({'get': 'list'})

        request: Request = self.factory.get(self.list_url)
        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        view_kwargs: dict[str, Any] = self.list_url_kwargs.copy()
        view_kwargs['telegram_bot_id'] = 0

        response: Response = view(request, **view_kwargs)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_invalid_id(self) -> None:
        view = MessageViewSet.as_view({'get': 'retrieve'})

        request: Request = self.factory.get(self.detail_url)
        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        view_kwargs: dict[str, Any] = self.detail_url_kwargs.copy()
        view_kwargs['id'] = 0

        response: Response = view(request, **view_kwargs)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_list(self) -> None:
        view = MessageViewSet.as_view({'get': 'list'})

        request: Request = self.factory.get(self.list_url)
        assert_view_basic_protected(
            view, request, self.user_access_token, **self.list_url_kwargs
        )

        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        response: Response = view(request, **self.list_url_kwargs)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_without_settings(self) -> None:
        view = MessageViewSet.as_view({'post': 'create'})

        request: Request = self.factory.post(
            self.list_url,
            {'name': 'Test name', 'text': 'The test message :)'},
            format='json',
        )
        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        response: Response = view(request, **self.list_url_kwargs)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_without_text(self) -> None:
        view = MessageViewSet.as_view({'post': 'create'})

        request: Request = self.factory.post(
            self.list_url,
            {
                'name': 'Test name',
                'settings': {
                    'reply_to_user_message': False,
                    'send_as_new_message': False,
                },
            },
            format='json',
        )
        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        response: Response = view(request, **self.list_url_kwargs)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_keyboard_without_text(self) -> None:
        view = MessageViewSet.as_view({'post': 'create'})

        request: Request = self.factory.post(
            self.list_url,
            {
                'name': 'Test name',
                'settings': {
                    'reply_to_user_message': False,
                    'send_as_new_message': False,
                },
                'keyboard': {
                    'type': KeyboardType.DEFAULT,
                    'buttons': [{'row': 0, 'position': 0, 'text': 'Test button text'}],
                },
            },
            format='json',
        )
        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        response: Response = view(request, **self.list_url_kwargs)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_default_keyboard_without_buttons(self) -> None:
        view = MessageViewSet.as_view({'post': 'create'})

        request: Request = self.factory.post(
            self.list_url,
            {
                'name': 'Test name',
                'settings': {
                    'reply_to_user_message': False,
                    'send_as_new_message': False,
                },
                'keyboard': {'type': KeyboardType.DEFAULT},
                'text': 'The test message :)',
            },
            format='json',
        )
        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        response: Response = view(request, **self.list_url_kwargs)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_default_keyboard_with_empty_buttons(self) -> None:
        view = MessageViewSet.as_view({'post': 'create'})

        request: Request = self.factory.post(
            self.list_url,
            {
                'name': 'Test name',
                'settings': {
                    'reply_to_user_message': False,
                    'send_as_new_message': False,
                },
                'keyboard': {'type': KeyboardType.DEFAULT, 'buttons': []},
                'text': 'The test message :)',
            },
            format='json',
        )
        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        response: Response = view(request, **self.list_url_kwargs)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_keyboard_buttons_over_limit(self) -> None:
        view = MessageViewSet.as_view({'post': 'create'})

        request: Request = self.factory.post(
            self.list_url,
            {
                'name': 'Test name',
                'settings': {
                    'reply_to_user_message': False,
                    'send_as_new_message': False,
                },
                'keyboard': {
                    'type': KeyboardType.DEFAULT,
                    'buttons': [
                        {'row': 0, 'position': num, 'text': f'Test button text #{num}'}
                        for num in range(
                            settings.TELEGRAM_BOT_MAX_MESSAGE_KEYBOARD_BUTTONS + 1
                        )
                    ],
                },
                'text': 'The test message :)',
            },
            format='json',
        )
        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        response: Response = view(request, **self.list_url_kwargs)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_removal_keyboard_with_buttons(self) -> None:
        view = MessageViewSet.as_view({'post': 'create'})

        request: Request = self.factory.post(
            self.list_url,
            {
                'name': 'Test name',
                'settings': {
                    'reply_to_user_message': False,
                    'send_as_new_message': False,
                },
                'keyboard': {
                    'type': KeyboardType.REMOVAL,
                    'buttons': [{'row': 0, 'position': 0, 'text': 'Test button text'}],
                },
                'text': 'The test message :)',
            },
            format='json',
        )
        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        response: Response = view(request, **self.list_url_kwargs)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_removal_keyboard_without_buttons(self) -> None:
        view = MessageViewSet.as_view({'post': 'create'})

        request: Request = self.factory.post(
            self.list_url,
            {
                'name': 'Test name',
                'settings': {
                    'reply_to_user_message': False,
                    'send_as_new_message': False,
                },
                'keyboard': {'type': KeyboardType.REMOVAL},
                'text': 'The test message :)',
            },
            format='json',
        )
        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        response: Response = view(request, **self.list_url_kwargs)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        new_message: Message = self.telegram_bot.messages.latest('id')
        self.assertEqual(new_message.keyboard.type, KeyboardType.REMOVAL)
        self.assertFalse(new_message.keyboard.buttons.exists())

    def test_create_over_limit(self) -> None:
        view = MessageViewSet.as_view({'post': 'create'})

        Message.objects.bulk_create(
            Message(
                telegram_bot=self.telegram_bot,
                name=f'Test message #{num}',
                text='The test message text',
            )
            for num in range(settings.TELEGRAM_BOT_MAX_MESSAGES)
        )

        request: Request = self.factory.post(
            self.list_url,
            {
                'name': 'Test name',
                'settings': {
                    'reply_to_user_message': False,
                    'send_as_new_message': False,
                },
                'text': 'The test message text :)',
            },
            format='json',
        )
        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        response: Response = view(request, **self.list_url_kwargs)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create(self) -> None:
        view = MessageViewSet.as_view({'post': 'create'})

        request: Request = self.factory.post(
            self.list_url,
            {
                'name': 'Test name',
                'settings': {
                    'reply_to_user_message': False,
                    'send_as_new_message': False,
                },
                'text': 'The test message :)',
            },
            format='json',
        )
        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        response: Response = view(request, **self.list_url_kwargs)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_retrieve(self) -> None:
        view = MessageViewSet.as_view({'get': 'retrieve'})

        request: Request = self.factory.get(self.detail_url)
        assert_view_basic_protected(
            view, request, self.user_access_token, **self.detail_url_kwargs
        )

        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        response: Response = view(request, **self.detail_url_kwargs)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_without_settings(self) -> None:
        view = MessageViewSet.as_view({'put': 'update'})

        request: Request = self.factory.put(
            self.detail_url, {'name': 'Test name 2'}, format='json'
        )
        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        response: Response = view(request, **self.detail_url_kwargs)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_removal_keyboard_with_buttons(self) -> None:
        view = MessageViewSet.as_view({'put': 'update'})

        request: Request = self.factory.put(
            self.detail_url,
            {
                'name': 'Test name 2',
                'settings': {
                    'reply_to_user_message': False,
                    'send_as_new_message': False,
                },
                'text': 'The test message text :)',
                'keyboard': {
                    'type': KeyboardType.REMOVAL,
                    'buttons': [{'row': 0, 'position': 0, 'text': 'Test button text'}],
                },
            },
            format='json',
        )
        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        response: Response = view(request, **self.detail_url_kwargs)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_removal_keyboard(self) -> None:
        view = MessageViewSet.as_view({'put': 'update'})

        request: Request = self.factory.put(
            self.detail_url,
            {
                'name': 'Test name 2',
                'settings': {
                    'reply_to_user_message': False,
                    'send_as_new_message': False,
                },
                'text': 'The test message text :)',
                'keyboard': {'type': KeyboardType.REMOVAL},
            },
            format='json',
        )
        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        response: Response = view(request, **self.detail_url_kwargs)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.keyboard.refresh_from_db()
        self.assertEqual(self.keyboard.type, KeyboardType.REMOVAL)
        self.assertFalse(self.keyboard.buttons.exists())

    def test_update(self) -> None:
        view = MessageViewSet.as_view({'put': 'update'})

        new_name: str = 'Test name 2'

        request: Request = self.factory.put(
            self.detail_url,
            {
                'name': new_name,
                'settings': {
                    'reply_to_user_message': False,
                    'send_as_new_message': False,
                },
                'text': 'The test message text :)',
            },
            format='json',
        )
        assert_view_basic_protected(
            view, request, self.user_access_token, **self.detail_url_kwargs
        )
        assert_view_requires_terms_acceptance(
            view, request, self.user, **self.detail_url_kwargs
        )

        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        response: Response = view(request, **self.detail_url_kwargs)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.message.refresh_from_db()
        self.assertEqual(self.message.name, new_name)

    def test_partial_update_removal_keyboard_with_buttons(self) -> None:
        view = MessageViewSet.as_view({'patch': 'partial_update'})

        request: Request = self.factory.patch(
            self.detail_url,
            {
                'keyboard': {
                    'type': KeyboardType.REMOVAL,
                    'buttons': [{'row': 0, 'position': 0, 'text': 'Test button text'}],
                },
            },
            format='json',
        )
        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        response: Response = view(request, **self.detail_url_kwargs)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_partial_update_removal_keyboard_buttons(self) -> None:
        view = MessageViewSet.as_view({'patch': 'partial_update'})

        self.keyboard.type = KeyboardType.REMOVAL
        self.keyboard.save(update_fields=['type'])

        request: Request = self.factory.patch(
            self.detail_url,
            {
                'keyboard': {
                    'buttons': [{'row': 0, 'position': 0, 'text': 'Test button text'}],
                },
            },
            format='json',
        )
        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        response: Response = view(request, **self.detail_url_kwargs)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_partial_update_removal_keyboard(self) -> None:
        view = MessageViewSet.as_view({'patch': 'partial_update'})

        request: Request = self.factory.patch(
            self.detail_url,
            {'keyboard': {'type': KeyboardType.REMOVAL}},
            format='json',
        )
        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        response: Response = view(request, **self.detail_url_kwargs)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.keyboard.refresh_from_db()
        self.assertEqual(self.keyboard.type, KeyboardType.REMOVAL)
        self.assertFalse(self.keyboard.buttons.exists())

    def test_partial_update(self) -> None:
        view = MessageViewSet.as_view({'patch': 'partial_update'})

        new_name: str = 'Test name 2'

        request: Request = self.factory.patch(
            self.detail_url, {'name': new_name}, format='json'
        )
        assert_view_basic_protected(
            view, request, self.user_access_token, **self.detail_url_kwargs
        )
        assert_view_requires_terms_acceptance(
            view, request, self.user, **self.detail_url_kwargs
        )

        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        response: Response = view(request, **self.detail_url_kwargs)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.message.refresh_from_db()
        self.assertEqual(self.message.name, new_name)

    def test_destroy(self) -> None:
        view = MessageViewSet.as_view({'delete': 'destroy'})

        request: Request = self.factory.delete(self.detail_url)
        assert_view_basic_protected(
            view, request, self.user_access_token, **self.detail_url_kwargs
        )
        assert_view_requires_terms_acceptance(
            view, request, self.user, **self.detail_url_kwargs
        )

        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        old_message_count: int = self.telegram_bot.messages.count()

        response: Response = view(request, **self.detail_url_kwargs)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(self.telegram_bot.messages.count(), old_message_count - 1)


class DiagramMessageViewSetTestCase(
    MessageMixin, TelegramBotMixin, UserMixin, TestCase
):
    def setUp(self) -> None:
        super().setUp()

        self.factory = APIRequestFactory()

        self.list_url_kwargs: dict[str, Any] = {'telegram_bot_id': self.telegram_bot.id}
        self.detail_url_kwargs: dict[str, Any] = {
            **self.list_url_kwargs,
            'id': self.message.id,
        }

        self.list_url: str = reverse(
            'api:telegram-bots:telegram-bot-diagram-message-list',
            kwargs=self.list_url_kwargs,
        )
        self.detail_url: str = reverse(
            'api:telegram-bots:telegram-bot-diagram-message-detail',
            kwargs=self.detail_url_kwargs,
        )

    def test_invalid_telegram_bot_id(self) -> None:
        view = DiagramMessageViewSet.as_view({'get': 'list'})

        request: Request = self.factory.get(self.list_url)
        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        view_kwargs: dict[str, Any] = self.list_url_kwargs.copy()
        view_kwargs['telegram_bot_id'] = 0

        response: Response = view(request, **view_kwargs)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_invalid_id(self) -> None:
        view = DiagramMessageViewSet.as_view({'get': 'retrieve'})

        request: Request = self.factory.get(self.detail_url)
        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        view_kwargs: dict[str, Any] = self.detail_url_kwargs.copy()
        view_kwargs['id'] = 0

        response: Response = view(request, **view_kwargs)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_retrieve(self) -> None:
        view = DiagramMessageViewSet.as_view({'get': 'retrieve'})

        request: Request = self.factory.get(self.detail_url)
        assert_view_basic_protected(
            view, request, self.user_access_token, **self.detail_url_kwargs
        )

        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        response: Response = view(request, **self.detail_url_kwargs)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_list(self) -> None:
        view = DiagramMessageViewSet.as_view({'get': 'list'})

        request: Request = self.factory.get(self.list_url)
        assert_view_basic_protected(
            view, request, self.user_access_token, **self.list_url_kwargs
        )

        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        response: Response = view(request, **self.list_url_kwargs)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update(self) -> None:
        view = DiagramMessageViewSet.as_view({'put': 'update'})

        new_x: int = 150

        request: Request = self.factory.put(
            self.detail_url, {'x': new_x, 'y': 200}, format='json'
        )
        assert_view_basic_protected(
            view, request, self.user_access_token, **self.detail_url_kwargs
        )
        assert_view_requires_terms_acceptance(
            view, request, self.user, **self.detail_url_kwargs
        )

        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        response: Response = view(request, **self.detail_url_kwargs)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.message.refresh_from_db()
        self.assertEqual(self.message.x, new_x)

    def test_partial_update(self) -> None:
        view = DiagramMessageViewSet.as_view({'patch': 'partial_update'})

        new_x: int = 150

        request: Request = self.factory.patch(
            self.detail_url, {'x': new_x}, format='json'
        )
        assert_view_basic_protected(
            view, request, self.user_access_token, **self.detail_url_kwargs
        )
        assert_view_requires_terms_acceptance(
            view, request, self.user, **self.detail_url_kwargs
        )

        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        response: Response = view(request, **self.detail_url_kwargs)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.message.refresh_from_db()
        self.assertEqual(self.message.x, new_x)
