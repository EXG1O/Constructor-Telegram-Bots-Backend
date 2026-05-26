from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory

from telegram_bots.models.trigger import Trigger, TriggerWebhook
from telegram_bots.tests.mixins import TelegramBotMixin
from users.tests.mixins import UserMixin

from .views import TriggerWebhookAPIView

from typing import TYPE_CHECKING


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
