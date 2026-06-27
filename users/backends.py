from django.conf import settings
from django.contrib.auth.backends import ModelBackend
from django.http import HttpRequest

from httpcore import ConnectionPool, Response
from jwt.types import Options
import jwt

from constructor_telegram_bots.http.exceptions import HTTPError

from .models import User

from http import HTTPMethod
from typing import Any
import base64
import json
import urllib.parse

TELEGRAM_LOGIN_HTTP_POOL = ConnectionPool(
    max_connections=100, max_keepalive_connections=20, keepalive_expiry=6
)


class TelegramBackend(ModelBackend):
    TOKEN_URL: str = 'https://oauth.telegram.org/token'
    JWKS_URL: str = 'https://oauth.telegram.org/.well-known/jwks.json'
    ISSUER: str = 'https://oauth.telegram.org'

    def _get_id_token(
        self, code: str, code_verifier: str, redirect_uri: str
    ) -> str | None:
        response: Response = TELEGRAM_LOGIN_HTTP_POOL.request(
            HTTPMethod.POST,
            self.TOKEN_URL,
            headers={
                'Content-Type': 'application/x-www-form-urlencoded',
                'Authorization': (
                    'Basic '
                    + base64.b64encode(
                        f'{settings.TELEGRAM_LOGIN_CLIENT_ID}:{settings.TELEGRAM_LOGIN_CLIENT_SECRET}'.encode()
                    ).decode()
                ),
            },
            content=urllib.parse.urlencode(
                {
                    'grant_type': 'authorization_code',
                    'client_id': settings.TELEGRAM_LOGIN_CLIENT_ID,
                    'code': code,
                    'code_verifier': code_verifier,
                    'redirect_uri': redirect_uri,
                }
            ).encode(),
        )

        if response.status != 200:
            return None

        return json.loads(response.content)['id_token']

    def _get_jwk(self, algorithm: str, key_id: str) -> jwt.PyJWK | None:
        response = TELEGRAM_LOGIN_HTTP_POOL.request(HTTPMethod.GET, self.JWKS_URL)

        if response.status != 200:
            raise HTTPError(response)

        keys: list[dict[str, Any]] = json.loads(response.content)['keys']

        for key in keys:
            if key.get('kid') == key_id and key.get('alg') == algorithm:
                return jwt.PyJWK(key)

        return None

    def authenticate(  # type: ignore [override]
        self, request: HttpRequest, code: str, redirect_uri: str, **kwargs: Any
    ) -> User | None:
        code_verifier: str | None = request.session.get('telegram_login_code_verifier')

        if not code_verifier:
            return None

        id_token: str | None = self._get_id_token(
            code=code, code_verifier=code_verifier, redirect_uri=redirect_uri
        )

        if not id_token:
            return None

        unverified_header: dict[str, Any] = jwt.get_unverified_header(id_token)
        header_alg: str = unverified_header['alg']

        if header_alg not in ('RS256', 'RS384', 'RS512'):
            return None

        jwk: jwt.PyJWK | None = self._get_jwk(
            algorithm=header_alg, key_id=unverified_header['kid']
        )

        if not jwk:
            return None

        claims: dict[str, Any] = jwt.decode(
            id_token,
            jwk,
            algorithms=[header_alg],
            options=Options(
                require=['iss', 'aud', 'sub', 'iat', 'exp', 'id', 'name'],
                verify_signature=True,
                verify_jti=False,
                verify_iss=True,
                verify_aud=True,
                strict_aud=True,
                verify_sub=True,
                verify_iat=True,
                verify_exp=True,
                verify_nbf=False,
                enforce_minimum_key_length=False,
            ),
            audience=str(settings.TELEGRAM_LOGIN_CLIENT_ID),
            issuer=self.ISSUER,
        )

        telegram_id: int = claims['id']
        full_name: str = claims['name']

        names: list[str] = full_name.split(maxsplit=1)
        first_name: str = names[0]
        last_name: str | None = names[1] if len(names) > 1 else None

        user, created = User.objects.get_or_create(
            telegram_id=telegram_id,
            defaults={'first_name': first_name, 'last_name': last_name},
        )

        if not created:
            user.first_name = first_name
            user.last_name = last_name
            user.save(update_fields=['first_name', 'last_name'])

        if not self.user_can_authenticate(user):
            return None

        return user
