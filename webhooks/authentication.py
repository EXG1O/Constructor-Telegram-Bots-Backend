from django.utils.translation import gettext as _

from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.request import Request

from telegram_bots.hub.models import TelegramBotsHub
from telegram_bots.models import TriggerWebhook


class TelegramAuthentication(BaseAuthentication):
    def authenticate(self, request: Request) -> tuple[TelegramBotsHub, str] | None:
        token: str | None = request.headers.get('X-Telegram-Bot-Api-Secret-Token')

        if not token:
            return None

        try:
            hub: TelegramBotsHub = TelegramBotsHub.objects.get(telegram_token=token)
        except TelegramBotsHub.DoesNotExist as error:
            raise AuthenticationFailed(_('Недействительный токен.')) from error

        return hub, token

    def authenticate_header(self, request: Request) -> str:
        return 'Telegram-Secret'


class TriggerWebhookAuthentication(BaseAuthentication):
    def authenticate(self, request: Request) -> tuple[TriggerWebhook, str]:
        id: int = request.parser_context['kwargs']['id']
        token: str = request.parser_context['kwargs']['token']

        try:
            webhook: TriggerWebhook = TriggerWebhook.objects.get(id=id, token=token)
        except TriggerWebhook.DoesNotExist as error:
            raise AuthenticationFailed() from error

        return webhook, token

    def authenticate_header(self, request: Request) -> str:
        return 'URL-Token'
