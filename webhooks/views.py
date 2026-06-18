from django.db.models import prefetch_related_objects

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from telegram_bots.hub.models import TelegramBotsHub
from telegram_bots.models import TelegramBot, Trigger, TriggerWebhook

from .authentication import TelegramAuthentication, TriggerWebhookAuthentication
from .exceptions import TelegramBotDisabledError
from .parsers import TriggerWebhookParser

from typing import cast


class TelegramAPIView(APIView):
    authentication_classes = [TelegramAuthentication]
    permission_classes = [IsAuthenticated]
    parser_classes = []

    def post(self, request: Request, bot_id: int) -> Response:
        hub = cast(TelegramBotsHub, request.user)
        hub.client.forward_telegram_data(bot_id=bot_id, data=request.body)

        return Response(status=status.HTTP_202_ACCEPTED)


class TriggerWebhookAPIView(APIView):
    authentication_classes = [TriggerWebhookAuthentication]
    permission_classes = [IsAuthenticated]
    parser_classes = [TriggerWebhookParser]

    def post(self, request: Request, id: int, token: str) -> Response:
        webhook = cast(TriggerWebhook, request.user)
        prefetch_related_objects([webhook], 'trigger__telegram_bot__hub')

        trigger: Trigger = webhook.trigger
        telegram_bot: TelegramBot = trigger.telegram_bot
        hub: TelegramBotsHub | None = telegram_bot.hub

        if not hub:
            raise TelegramBotDisabledError()

        hub.client.send_trigger(
            bot_id=telegram_bot.id,
            trigger=trigger,
            trigger_has_target_connections=trigger.target_connections.exists(),
            payload=request.data,
        )

        return Response(status=status.HTTP_202_ACCEPTED)
