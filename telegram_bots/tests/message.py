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

from ..models import Message
from ..views import DiagramMessageViewSet, MessageViewSet
from .mixins import MessageMixin, TelegramBotMixin

from contextlib import suppress
from typing import TYPE_CHECKING


class MessageViewSetTests(MessageMixin, TelegramBotMixin, UserMixin, TestCase):
    def setUp(self) -> None:
        super().setUp()

        self.factory = APIRequestFactory()

        self.list_true_url: str = reverse(
            'api:telegram-bots:telegram-bot-message-list',
            kwargs={'telegram_bot_id': self.telegram_bot.id},
        )
        self.list_false_url: str = reverse(
            'api:telegram-bots:telegram-bot-message-list', kwargs={'telegram_bot_id': 0}
        )
        self.detail_true_url: str = reverse(
            'api:telegram-bots:telegram-bot-message-detail',
            kwargs={'telegram_bot_id': self.telegram_bot.id, 'id': self.message.id},
        )
        self.detail_false_url_1: str = reverse(
            'api:telegram-bots:telegram-bot-message-detail',
            kwargs={'telegram_bot_id': 0, 'id': self.message.id},
        )
        self.detail_false_url_2: str = reverse(
            'api:telegram-bots:telegram-bot-message-detail',
            kwargs={'telegram_bot_id': self.telegram_bot.id, 'id': 0},
        )

    def test_list(self) -> None:
        view = MessageViewSet.as_view({'get': 'list'})

        if TYPE_CHECKING:
            request: Request
            response: Response

        request = self.factory.get(self.list_true_url)
        assert_view_basic_protected(
            view, request, self.user_access_token, telegram_bot_id=self.telegram_bot.id
        )

        request = self.factory.get(self.list_false_url)
        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        response = view(request, telegram_bot_id=0)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        request = self.factory.get(self.list_true_url)
        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        response = view(request, telegram_bot_id=self.telegram_bot.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create(self) -> None:
        view = MessageViewSet.as_view({'post': 'create'})

        if TYPE_CHECKING:
            request: Request
            response: Response

        request = self.factory.post(self.list_true_url)
        assert_view_basic_protected(
            view, request, self.user_access_token, telegram_bot_id=self.telegram_bot.id
        )
        assert_view_requires_terms_acceptance(
            view, request, self.user, telegram_bot_id=self.telegram_bot.id
        )

        request = self.factory.post(self.list_false_url)
        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        response = view(request, telegram_bot_id=0)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        request = self.factory.post(self.list_true_url)
        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        response = view(request, telegram_bot_id=self.telegram_bot.id)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        request = self.factory.post(
            self.list_true_url,
            {'name': 'Test name', 'text': 'The test message :)'},
            format='json',
        )
        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        response = view(request, telegram_bot_id=self.telegram_bot.id)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        request = self.factory.post(
            self.list_true_url,
            {
                'name': 'Test name',
                'settings': {
                    'reply_to_user_message': False,
                    'delete_user_message': False,
                    'send_as_new_message': False,
                },
            },
            format='json',
        )
        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        response = view(request, telegram_bot_id=self.telegram_bot.id)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        request = self.factory.post(
            self.list_true_url,
            {
                'name': 'Test name',
                'settings': {
                    'reply_to_user_message': False,
                    'delete_user_message': False,
                    'send_as_new_message': False,
                },
                'keyboard': {
                    'buttons': [{'row': 0, 'position': 0, 'text': 'Test button text'}]
                },
            },
            format='json',
        )
        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        response = view(request, telegram_bot_id=self.telegram_bot.id)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        request = self.factory.post(
            self.list_true_url,
            {
                'name': 'Test name',
                'settings': {
                    'reply_to_user_message': False,
                    'delete_user_message': False,
                    'send_as_new_message': False,
                },
                'keyboard': {
                    'buttons': [
                        {'row': 0, 'position': num, 'text': f'Test button text #{num}'}
                        for num in range(
                            settings.TELEGRAM_BOT_MAX_MESSAGE_KEYBOARD_BUTTONS + 1
                        )
                    ]
                },
                'text': 'The test message :)',
            },
            format='json',
        )
        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        response = view(request, telegram_bot_id=self.telegram_bot.id)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        request = self.factory.post(
            self.list_true_url,
            {
                'name': 'Test name',
                'settings': {
                    'reply_to_user_message': False,
                    'delete_user_message': False,
                    'send_as_new_message': False,
                },
                'text': 'The test message :)',
            },
            format='json',
        )
        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        old_message_count: int = self.telegram_bot.messages.count()

        response = view(request, telegram_bot_id=self.telegram_bot.id)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(self.telegram_bot.messages.count(), old_message_count + 1)

        Message.objects.bulk_create(
            Message(
                telegram_bot=self.telegram_bot,
                name=f'Test message #{num}',
                text='The test message text',
            )
            for num in range(settings.TELEGRAM_BOT_MAX_MESSAGES)
        )

        request = self.factory.post(
            self.list_true_url,
            {
                'name': 'Test name',
                'settings': {
                    'reply_to_user_message': False,
                    'delete_user_message': False,
                    'send_as_new_message': False,
                },
                'text': 'The test message text :)',
            },
            format='json',
        )
        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        response = view(request, telegram_bot_id=self.telegram_bot.id)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve(self) -> None:
        view = MessageViewSet.as_view({'get': 'retrieve'})

        if TYPE_CHECKING:
            request: Request
            response: Response

        request = self.factory.get(self.detail_true_url)
        assert_view_basic_protected(
            view,
            request,
            self.user_access_token,
            telegram_bot_id=self.telegram_bot.id,
            id=self.message.id,
        )

        for url in [self.detail_false_url_1, self.detail_false_url_2]:
            request = self.factory.get(url)
            force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

            response = view(request, telegram_bot_id=0, id=self.message.id)
            self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        request = self.factory.get(self.detail_true_url)
        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        response = view(
            request, telegram_bot_id=self.telegram_bot.id, id=self.message.id
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update(self) -> None:
        view = MessageViewSet.as_view({'put': 'update'})

        if TYPE_CHECKING:
            request: Request
            response: Response

        request = self.factory.put(self.detail_true_url)
        assert_view_basic_protected(
            view,
            request,
            self.user_access_token,
            telegram_bot_id=self.telegram_bot.id,
            id=self.message.id,
        )
        assert_view_requires_terms_acceptance(
            view,
            request,
            self.user,
            telegram_bot_id=self.telegram_bot.id,
            id=self.message.id,
        )

        for url in [self.detail_false_url_1, self.detail_false_url_2]:
            request = self.factory.put(url)
            force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

            response = view(request, telegram_bot_id=0, id=self.message.id)
            self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        request = self.factory.put(self.detail_true_url)
        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        response = view(
            request, telegram_bot_id=self.telegram_bot.id, id=self.message.id
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        new_name: str = 'Test name 2'

        request = self.factory.put(
            self.detail_true_url, {'name': new_name}, format='json'
        )
        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        response = view(
            request, telegram_bot_id=self.telegram_bot.id, id=self.message.id
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        request = self.factory.put(
            self.detail_true_url,
            {
                'name': new_name,
                'settings': {
                    'reply_to_user_message': False,
                    'delete_user_message': False,
                    'send_as_new_message': False,
                },
                'text': 'The test message text :)',
            },
            format='json',
        )
        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        response = view(
            request, telegram_bot_id=self.telegram_bot.id, id=self.message.id
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.message.refresh_from_db()
        self.assertEqual(self.message.name, new_name)

    def test_partial_update(self) -> None:
        view = MessageViewSet.as_view({'patch': 'partial_update'})

        if TYPE_CHECKING:
            request: Request
            response: Response

        request = self.factory.patch(self.detail_true_url)
        assert_view_basic_protected(
            view,
            request,
            self.user_access_token,
            telegram_bot_id=self.telegram_bot.id,
            id=self.message.id,
        )
        assert_view_requires_terms_acceptance(
            view,
            request,
            self.user,
            telegram_bot_id=self.telegram_bot.id,
            id=self.message.id,
        )

        for url in [self.detail_false_url_1, self.detail_false_url_2]:
            request = self.factory.patch(url)
            force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

            response = view(request, telegram_bot_id=0, id=self.message.id)
            self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        request = self.factory.patch(self.detail_true_url)
        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        response = view(
            request, telegram_bot_id=self.telegram_bot.id, id=self.message.id
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        new_name: str = 'Test name 2'

        request = self.factory.patch(
            self.detail_true_url, {'name': new_name}, format='json'
        )
        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        response = view(
            request, telegram_bot_id=self.telegram_bot.id, id=self.message.id
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.message.refresh_from_db()
        self.assertEqual(self.message.name, new_name)

    def test_destroy(self) -> None:
        view = MessageViewSet.as_view({'delete': 'destroy'})

        if TYPE_CHECKING:
            request: Request
            response: Response

        request = self.factory.delete(self.detail_true_url)
        assert_view_basic_protected(
            view,
            request,
            self.user_access_token,
            telegram_bot_id=self.telegram_bot.id,
            id=self.message.id,
        )
        assert_view_requires_terms_acceptance(
            view,
            request,
            self.user,
            telegram_bot_id=self.telegram_bot.id,
            id=self.message.id,
        )

        for url in [self.detail_false_url_1, self.detail_false_url_2]:
            request = self.factory.delete(url)
            force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

            response = view(request, telegram_bot_id=0, id=self.message.id)
            self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        request = self.factory.delete(self.detail_true_url)
        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        response = view(
            request, telegram_bot_id=self.telegram_bot.id, id=self.message.id
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        with suppress(Message.DoesNotExist):
            self.message.refresh_from_db()
            raise self.failureException('Message has not been deleted from database!')


class DiagramMessageViewSetTests(MessageMixin, TelegramBotMixin, UserMixin, TestCase):
    def setUp(self) -> None:
        super().setUp()

        self.factory = APIRequestFactory()

        self.list_true_url: str = reverse(
            'api:telegram-bots:telegram-bot-diagram-message-list',
            kwargs={'telegram_bot_id': self.telegram_bot.id},
        )
        self.list_false_url: str = reverse(
            'api:telegram-bots:telegram-bot-diagram-message-list',
            kwargs={'telegram_bot_id': 0},
        )
        self.detail_true_url: str = reverse(
            'api:telegram-bots:telegram-bot-diagram-message-detail',
            kwargs={'telegram_bot_id': self.telegram_bot.id, 'id': self.message.id},
        )
        self.detail_false_url_1: str = reverse(
            'api:telegram-bots:telegram-bot-diagram-message-detail',
            kwargs={'telegram_bot_id': 0, 'id': self.message.id},
        )
        self.detail_false_url_2: str = reverse(
            'api:telegram-bots:telegram-bot-diagram-message-detail',
            kwargs={'telegram_bot_id': self.telegram_bot.id, 'id': 0},
        )

    def test_retrieve(self) -> None:
        view = DiagramMessageViewSet.as_view({'get': 'retrieve'})

        if TYPE_CHECKING:
            request: Request
            response: Response

        request = self.factory.get(self.detail_true_url)
        assert_view_basic_protected(
            view, request, self.user_access_token, telegram_bot_id=self.telegram_bot.id
        )

        for url in [self.detail_false_url_1, self.detail_false_url_2]:
            request = self.factory.get(url)
            force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

            response = view(request, telegram_bot_id=0, id=self.message.id)
            self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        request = self.factory.get(self.detail_true_url)
        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        response = view(
            request, telegram_bot_id=self.telegram_bot.id, id=self.message.id
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_list(self) -> None:
        view = DiagramMessageViewSet.as_view({'get': 'list'})

        if TYPE_CHECKING:
            request: Request
            response: Response

        request = self.factory.get(self.list_true_url)
        assert_view_basic_protected(
            view, request, self.user_access_token, telegram_bot_id=self.telegram_bot.id
        )

        request = self.factory.get(self.list_false_url)
        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        response = view(request, telegram_bot_id=0)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        request = self.factory.get(self.list_true_url)
        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        response = view(request, telegram_bot_id=self.telegram_bot.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update(self) -> None:
        view = DiagramMessageViewSet.as_view({'put': 'update'})

        if TYPE_CHECKING:
            request: Request
            response: Response

        request = self.factory.put(self.detail_true_url)
        assert_view_basic_protected(
            view,
            request,
            self.user_access_token,
            telegram_bot_id=self.telegram_bot.id,
            id=self.message.id,
        )
        assert_view_requires_terms_acceptance(
            view,
            request,
            self.user,
            telegram_bot_id=self.telegram_bot.id,
            id=self.message.id,
        )

        for url in [self.detail_false_url_1, self.detail_false_url_2]:
            request = self.factory.put(url)
            force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

            response = view(request, telegram_bot_id=0, id=self.message.id)
            self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        request = self.factory.put(self.detail_true_url)
        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        response = view(
            request, telegram_bot_id=self.telegram_bot.id, id=self.message.id
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        new_x: int = 150

        request = self.factory.put(
            self.detail_true_url, {'x': new_x, 'y': 200}, format='json'
        )
        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        response = view(
            request, telegram_bot_id=self.telegram_bot.id, id=self.message.id
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.message.refresh_from_db()
        self.assertEqual(self.message.x, new_x)

    def test_partial_update(self) -> None:
        view = DiagramMessageViewSet.as_view({'patch': 'partial_update'})

        if TYPE_CHECKING:
            request: Request
            response: Response

        request = self.factory.patch(self.detail_true_url)
        assert_view_basic_protected(
            view,
            request,
            self.user_access_token,
            telegram_bot_id=self.telegram_bot.id,
            id=self.message.id,
        )
        assert_view_requires_terms_acceptance(
            view,
            request,
            self.user,
            telegram_bot_id=self.telegram_bot.id,
            id=self.message.id,
        )

        for url in [self.detail_false_url_1, self.detail_false_url_2]:
            request = self.factory.patch(url)
            force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

            response = view(request, telegram_bot_id=0, id=self.message.id)
            self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        request = self.factory.patch(self.detail_true_url)
        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        response = view(
            request, telegram_bot_id=self.telegram_bot.id, id=self.message.id
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        new_x: int = 150

        request = self.factory.patch(self.detail_true_url, {'x': new_x}, format='json')
        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        response = view(
            request, telegram_bot_id=self.telegram_bot.id, id=self.message.id
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.message.refresh_from_db()
        self.assertEqual(self.message.x, new_x)
