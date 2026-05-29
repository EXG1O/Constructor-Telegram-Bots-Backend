from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory, force_authenticate

from constructor_telegram_bots.utils.tests import assert_view_basic_protected
from users.tests.mixins import UserMixin

from ...tests.mixins import ConditionMixin, TelegramBotMixin
from ..views import ConditionViewSet
from .mixins import HubMixin

from typing import TYPE_CHECKING


class ConditionViewSetTests(
    ConditionMixin, HubMixin, TelegramBotMixin, UserMixin, TestCase
):
    def setUp(self) -> None:
        super().setUp()

        self.factory = APIRequestFactory()

        self.list_true_url: str = reverse(
            'api:telegram-bots-hub:telegram-bot-condition-list',
            kwargs={'telegram_bot_id': self.telegram_bot.id},
        )
        self.list_false_url: str = reverse(
            'api:telegram-bots-hub:telegram-bot-condition-list',
            kwargs={'telegram_bot_id': 0},
        )
        self.detail_true_url: str = reverse(
            'api:telegram-bots-hub:telegram-bot-condition-detail',
            kwargs={'telegram_bot_id': self.telegram_bot.id, 'id': self.condition.id},
        )
        self.detail_false_url_1: str = reverse(
            'api:telegram-bots-hub:telegram-bot-condition-detail',
            kwargs={'telegram_bot_id': 0, 'id': self.condition.id},
        )
        self.detail_false_url_2: str = reverse(
            'api:telegram-bots-hub:telegram-bot-condition-detail',
            kwargs={'telegram_bot_id': self.telegram_bot.id, 'id': 0},
        )

    def test_list(self) -> None:
        view = ConditionViewSet.as_view({'get': 'list'})

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

    def test_retrieve(self) -> None:
        view = ConditionViewSet.as_view({'get': 'retrieve'})

        if TYPE_CHECKING:
            request: Request
            response: Response

        request = self.factory.get(self.detail_true_url)
        assert_view_basic_protected(
            view,
            request,
            self.hub.service_token,
            telegram_bot_id=self.telegram_bot.id,
            id=self.condition.id,
        )

        for url in [self.detail_false_url_1, self.detail_false_url_2]:
            request = self.factory.get(url)
            force_authenticate(request, self.hub, self.hub.service_token)  # type: ignore [arg-type]

            response = view(request, telegram_bot_id=0, id=self.condition.id)
            self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        request = self.factory.get(self.detail_true_url)
        force_authenticate(request, self.hub, self.hub.service_token)  # type: ignore [arg-type]

        response = view(
            request, telegram_bot_id=self.telegram_bot.id, id=self.condition.id
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
