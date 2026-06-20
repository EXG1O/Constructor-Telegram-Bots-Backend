from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory, force_authenticate

from constructor_telegram_bots.utils.tests import assert_view_basic_protected
from users.tests.mixins import UserMixin

from ...enums import ChatType
from ...tests.mixins import BotChatMixin, BotUserMixin, TelegramBotMixin
from ..views import ChatViewSet
from .mixins import HubMixin

from typing import TYPE_CHECKING


class ChatViewSetTests(
    BotUserMixin, BotChatMixin, HubMixin, TelegramBotMixin, UserMixin, TestCase
):
    def setUp(self) -> None:
        super().setUp()

        self.factory = APIRequestFactory()

        self.list_true_url: str = reverse(
            'api:telegram-bots-hub:telegram-bot-chat-list',
            kwargs={'telegram_bot_id': self.telegram_bot.id},
        )
        self.list_false_url: str = reverse(
            'api:telegram-bots-hub:telegram-bot-chat-list',
            kwargs={'telegram_bot_id': 0},
        )
        self.detail_true_url: str = reverse(
            'api:telegram-bots-hub:telegram-bot-chat-detail',
            kwargs={'telegram_bot_id': self.telegram_bot.id, 'id': self.bot_chat.id},
        )
        self.detail_false_url_1: str = reverse(
            'api:telegram-bots-hub:telegram-bot-chat-detail',
            kwargs={'telegram_bot_id': 0, 'id': self.bot_chat.id},
        )
        self.detail_false_url_2: str = reverse(
            'api:telegram-bots-hub:telegram-bot-chat-detail',
            kwargs={'telegram_bot_id': self.telegram_bot.id, 'id': 0},
        )

    def test_list(self) -> None:
        view = ChatViewSet.as_view({'get': 'list'})

        if TYPE_CHECKING:
            request: Request
            response: Response

        request = self.factory.get(self.list_true_url)
        assert_view_basic_protected(
            view, request, self.hub.service_token, telegram_bot_id=self.telegram_bot.id
        )

        request = self.factory.get(self.list_false_url)
        force_authenticate(request, self.hub, self.hub.service_token)  # type: ignore [arg-type]

        response = view(request, telegram_bot_id=0)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        request = self.factory.get(self.list_true_url)
        force_authenticate(request, self.hub, self.hub.service_token)  # type: ignore [arg-type]

        response = view(request, telegram_bot_id=self.telegram_bot.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create(self) -> None:
        view = ChatViewSet.as_view({'post': 'create'})

        if TYPE_CHECKING:
            request: Request
            response: Response

        request = self.factory.post(self.list_true_url)
        assert_view_basic_protected(
            view, request, self.hub.service_token, telegram_bot_id=self.telegram_bot.id
        )

        request = self.factory.post(self.list_false_url)
        force_authenticate(request, self.hub, self.hub.service_token)  # type: ignore [arg-type]

        response = view(request, telegram_bot_id=0)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        old_bot_chat_count: int = self.telegram_bot.chats.count()

        request = self.factory.post(
            self.list_true_url,
            {
                'telegram_id': 1,
                'type': ChatType.PRIVATE,
                'first_name': 'Durov',
                'last_name': '<3',
            },
            format='json',
        )
        force_authenticate(request, self.hub, self.hub.service_token)  # type: ignore [arg-type]

        response = view(request, telegram_bot_id=self.telegram_bot.id)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(self.telegram_bot.chats.count(), old_bot_chat_count + 1)

    def test_retrieve(self) -> None:
        view = ChatViewSet.as_view({'get': 'retrieve'})

        if TYPE_CHECKING:
            request: Request
            response: Response

        request = self.factory.get(self.detail_true_url)
        assert_view_basic_protected(
            view,
            request,
            self.hub.service_token,
            telegram_bot_id=self.telegram_bot.id,
            id=self.bot_chat.id,
        )

        for url in [self.detail_false_url_1, self.detail_false_url_2]:
            request = self.factory.get(url)
            force_authenticate(request, self.hub, self.hub.service_token)  # type: ignore [arg-type]

            response = view(request, telegram_bot_id=0, id=self.bot_chat.id)
            self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        request = self.factory.get(self.detail_true_url)
        force_authenticate(request, self.hub, self.hub.service_token)  # type: ignore [arg-type]

        response = view(
            request, telegram_bot_id=self.telegram_bot.id, id=self.bot_chat.id
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_users(self) -> None:
        view = ChatViewSet.as_view({'post': 'users'})

        true_url: str = reverse(
            'api:telegram-bots-hub:telegram-bot-chat-users',
            kwargs={'telegram_bot_id': self.telegram_bot.id, 'id': self.bot_chat.id},
        )
        false_url_1: str = reverse(
            'api:telegram-bots-hub:telegram-bot-chat-users',
            kwargs={'telegram_bot_id': 0, 'id': self.bot_chat.id},
        )
        false_url_2: str = reverse(
            'api:telegram-bots-hub:telegram-bot-chat-users',
            kwargs={'telegram_bot_id': self.telegram_bot.id, 'id': 0},
        )

        if TYPE_CHECKING:
            request: Request
            response: Response

        request = self.factory.post(true_url, format='json')
        assert_view_basic_protected(
            view,
            request,
            self.hub.service_token,
            telegram_bot_id=self.telegram_bot.id,
            id=self.bot_chat.id,
        )

        for url in [false_url_1, false_url_2]:
            request = self.factory.post(url, format='json')
            force_authenticate(request, self.hub, self.hub.service_token)  # type: ignore [arg-type]

            response = view(request, telegram_bot_id=0, id=self.bot_chat.id)
            self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        request = self.factory.post(true_url, [], format='json')
        force_authenticate(request, self.hub, self.hub.service_token)  # type: ignore [arg-type]

        response = view(
            request, telegram_bot_id=self.telegram_bot.id, id=self.bot_chat.id
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        request = self.factory.post(true_url, [{'id': 0}], format='json')
        force_authenticate(request, self.hub, self.hub.service_token)  # type: ignore [arg-type]

        response = view(
            request, telegram_bot_id=self.telegram_bot.id, id=self.bot_chat.id
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        old_chat_users_count: int = self.bot_chat.users.count()

        request = self.factory.post(
            true_url,
            [{'id': self.user.id}, {'telegram_id': self.user.telegram_id}],
            format='json',
        )
        force_authenticate(request, self.hub, self.hub.service_token)  # type: ignore [arg-type]

        response = view(
            request, telegram_bot_id=self.telegram_bot.id, id=self.bot_chat.id
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(self.bot_chat.users.count(), old_chat_users_count + 1)
