from rest_framework.authentication import TokenAuthentication as BaseTokenAuthentication

from constructor_telegram_bots.exceptions import InvalidTokenError

from .models import TelegramBotsHub


class TokenAuthentication(BaseTokenAuthentication):
    def authenticate_credentials(self, token: str) -> tuple[TelegramBotsHub, str]:
        try:
            hub: TelegramBotsHub = TelegramBotsHub.objects.get(service_token=token)
        except TelegramBotsHub.DoesNotExist as error:
            raise InvalidTokenError() from error

        return hub, token
