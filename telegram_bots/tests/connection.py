from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory, force_authenticate

from constructor_telegram_bots.utils.tests import assert_view_basic_protected
from users.tests.mixins import UserMixin
from users.utils.tests import assert_view_requires_terms_acceptance

from ..enums import ConnectionHandlePosition, ConnectionObjectType, KeyboardType
from ..models import Connection, Message, MessageKeyboard, MessageKeyboardButton
from ..views import ConnectionViewSet
from .mixins import TelegramBotMixin

from contextlib import suppress
from typing import TYPE_CHECKING


class ConnectionViewSetTests(TelegramBotMixin, UserMixin, TestCase):
    def setUp(self) -> None:
        super().setUp()

        self.factory = APIRequestFactory()

        self.message_1: Message = self.telegram_bot.messages.create(
            name='Test name 1', text='...'
        )

        self.message_2: Message = self.telegram_bot.messages.create(
            name='Test name 2', text='...'
        )
        self.message_2_keyboard: MessageKeyboard = MessageKeyboard.objects.create(
            message=self.message_2, type=KeyboardType.DEFAULT
        )
        self.message_2_keyboard_button: MessageKeyboardButton = (
            self.message_2_keyboard.buttons.create(row=0, position=0, text='Button')
        )

        self.connection: Connection = self.telegram_bot.connections.create(
            source_object=self.message_2_keyboard_button, target_object=self.message_1
        )

        self.list_true_url: str = reverse(
            'api:telegram-bots:telegram-bot-connection-list',
            kwargs={'telegram_bot_id': self.telegram_bot.id},
        )
        self.list_false_url: str = reverse(
            'api:telegram-bots:telegram-bot-connection-list',
            kwargs={'telegram_bot_id': 0},
        )
        self.detail_true_url: str = reverse(
            'api:telegram-bots:telegram-bot-connection-detail',
            kwargs={'telegram_bot_id': self.telegram_bot.id, 'id': self.connection.id},
        )
        self.detail_false_url_1: str = reverse(
            'api:telegram-bots:telegram-bot-connection-detail',
            kwargs={'telegram_bot_id': 0, 'id': self.connection.id},
        )
        self.detail_false_url_2: str = reverse(
            'api:telegram-bots:telegram-bot-connection-detail',
            kwargs={'telegram_bot_id': self.telegram_bot.id, 'id': 0},
        )

    def test_create(self) -> None:
        view = ConnectionViewSet.as_view({'post': 'create'})

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

        request = self.factory.post(
            self.list_true_url,
            {
                'source_object_type': ConnectionObjectType.MESSAGE_KEYBOARD_BUTTON,
                'source_object_id': self.message_2_keyboard_button.id,
                'source_handle_position': ConnectionHandlePosition.RIGHT,
                'target_object_type': ConnectionObjectType.MESSAGE,
                'target_object_id': self.message_1.id,
                'target_handle_position': ConnectionHandlePosition.LEFT,
            },
            format='json',
        )
        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        old_message_1_target_connection_count: int = (
            self.message_1.target_connections.count()
        )
        old_message_2_keyboard_button_source_connection_count: int = (
            self.message_2_keyboard_button.source_connections.count()
        )

        response = view(request, telegram_bot_id=self.telegram_bot.id)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            self.message_1.target_connections.count(),
            old_message_1_target_connection_count + 1,
        )
        self.assertEqual(
            self.message_2_keyboard_button.source_connections.count(),
            old_message_2_keyboard_button_source_connection_count + 1,
        )

    def test_destroy(self) -> None:
        view = ConnectionViewSet.as_view({'delete': 'destroy'})

        if TYPE_CHECKING:
            request: Request
            response: Response

        request = self.factory.delete(self.detail_true_url)
        assert_view_basic_protected(
            view,
            request,
            self.user_access_token,
            telegram_bot_id=self.telegram_bot.id,
            id=self.connection.id,
        )
        assert_view_requires_terms_acceptance(
            view,
            request,
            self.user,
            telegram_bot_id=self.telegram_bot.id,
            id=self.connection.id,
        )

        for url in [self.detail_false_url_1, self.detail_false_url_2]:
            request = self.factory.delete(url)
            force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

            response = view(request, telegram_bot_id=self.telegram_bot.id, id=0)
            self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        request = self.factory.delete(self.detail_true_url)
        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        response = view(
            request, telegram_bot_id=self.telegram_bot.id, id=self.connection.id
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        with suppress(Connection.DoesNotExist):
            self.connection.refresh_from_db()
            raise self.failureException(
                'Connection has not been deleted from database!'
            )
