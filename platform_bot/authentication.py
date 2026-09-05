from django.conf import settings

from rest_framework.authentication import TokenAuthentication as BaseTokenAuthentication

from constructor_telegram_bots.exceptions import InvalidTokenError

from .models import PlatformBot

import secrets


class TokenAuthentication(BaseTokenAuthentication):
    def authenticate_credentials(self, token: str) -> tuple[PlatformBot, str]:
        if not secrets.compare_digest(token, settings.PLATFORM_BOT_SERVICE_TOKEN):
            raise InvalidTokenError()
        return PlatformBot(), token
