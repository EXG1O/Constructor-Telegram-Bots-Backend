from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory, force_authenticate

from constructor_telegram_bots.utils.tests import assert_view_basic_protected
from telegram_bots.hub.tests.mixins import HubMixin
from telegram_bots.models.trigger import Trigger, TriggerWebhook
from telegram_bots.tests.mixins import TelegramBotMixin
from users.tests.mixins import UserMixin

from .views import TelegramAPIView, TriggerWebhookAPIView

from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock, patch
import json


class TelegramAPIViewTests(TelegramBotMixin, UserMixin, HubMixin, TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.factory = APIRequestFactory()

    @patch('telegram_bots.hub.models.TelegramBotsHub.client')
    def test_post(self, mock_client: MagicMock) -> None:
        view = TelegramAPIView.as_view()
        data: dict[str, Any] = {'key': 'value'}

        request: Request = self.factory.post(
            reverse('api:webhooks:telegram', kwargs={'bot_id': self.telegram_bot.id}),
            data=data,
            content_type='application/json',
        )
        assert_view_basic_protected(
            view, request, self.hub.telegram_token, bot_id=self.telegram_bot.id
        )
        force_authenticate(request, self.hub, self.hub.telegram_token)  # type: ignore [arg-type]

        response: Response = view(request, bot_id=self.telegram_bot.id)
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        mock_client.forward_telegram_data.assert_called_once_with(
            bot_id=self.telegram_bot.id, data=json.dumps(data).encode()
        )


class TriggerWebhookAPIViewTests(TelegramBotMixin, UserMixin, TestCase):
    def setUp(self) -> None:
        super().setUp()

        self.trigger: Trigger = self.telegram_bot.triggers.create(name='Test name')
        self.trigger_webhook: TriggerWebhook = TriggerWebhook.objects.create(
            trigger=self.trigger
        )

        self.factory = APIRequestFactory()

    def test_post(self) -> None:
        view = TriggerWebhookAPIView.as_view()

        if TYPE_CHECKING:
            response: Response

        request: Request = self.factory.post(
            reverse(
                'api:webhooks:trigger',
                kwargs={
                    'id': self.trigger_webhook.id,
                    'token': self.trigger_webhook.token,
                },
            )
        )

        response = view(request, id=None, token=None)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        response = view(
            request, id=self.trigger_webhook.id, token=self.trigger_webhook.token
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.telegram_bot.must_be_enabled = True
        self.telegram_bot.save(update_fields=['must_be_enabled'])

        response = view(
            request, id=self.trigger_webhook.id, token=self.trigger_webhook.token
        )
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
