from django.conf import settings

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from telegram_bots.hub.models import TelegramBotsHub
from telegram_bots.models import TelegramBot, Trigger, TriggerWebhook

from .authentication import TriggerWebhookAuthentication
from .exceptions import TelegramBotDisabledError
from .parsers import TriggerWebhookParser

from typing import cast


class TriggerWebhookAPIView(APIView):
    authentication_classes = [TriggerWebhookAuthentication]
    permission_classes = [IsAuthenticated]
    parser_classes = [TriggerWebhookParser]

    def post(self, request: Request, id: int, token: str) -> Response:
        webhook = cast(TriggerWebhook, request.user)
        trigger: Trigger = webhook.trigger
        telegram_bot: TelegramBot = trigger.telegram_bot

        if settings.TEST:
            if not telegram_bot.must_be_enabled:
                raise TelegramBotDisabledError()
        else:
            try:
                hub: TelegramBotsHub = telegram_bot.hub
            except TelegramBotsHub.DoesNotExist as error:
                raise TelegramBotDisabledError() from error

            hub.client.send_trigger(
                bot_id=telegram_bot.id, trigger=trigger, payload=request.data
            )

        return Response(status=status.HTTP_202_ACCEPTED)
