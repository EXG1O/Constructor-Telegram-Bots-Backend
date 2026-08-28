from django.conf import settings
from django.contrib.auth.backends import ModelBackend
from django.http import HttpRequest

from jwt.types import Options
import httpx
import jwt

from .models import User

from typing import TYPE_CHECKING, Any, Final, cast

_telegram_login_client = httpx.Client(
    headers={'User-Agent': settings.APP_USER_AGENT},
    limits=httpx.Limits(
        max_connections=25, max_keepalive_connections=10, keepalive_expiry=6
    ),
    transport=httpx.HTTPTransport(trust_env=False, retries=2),
)


class TelegramBackend(ModelBackend):
    TOKEN_URL: Final[str] = 'https://oauth.telegram.org/token'
    JWKS_URL: Final[str] = 'https://oauth.telegram.org/.well-known/jwks.json'
    ISSUER: Final[str] = 'https://oauth.telegram.org'

    def _get_id_token(
        self, code: str, code_verifier: str, redirect_uri: str
    ) -> str | None:
        response: httpx.Response = _telegram_login_client.post(
            self.TOKEN_URL,
            auth=httpx.BasicAuth(
                username=str(settings.TELEGRAM_LOGIN_CLIENT_ID),
                password=settings.TELEGRAM_LOGIN_CLIENT_SECRET,
            ),
            data={
                'grant_type': 'authorization_code',
                'client_id': settings.TELEGRAM_LOGIN_CLIENT_ID,
                'code': code,
                'code_verifier': code_verifier,
                'redirect_uri': redirect_uri,
            },
        )

        if not response.is_success:
            return None

        return response.json()['id_token']

    def _get_jwk(self, algorithm: str, key_id: str) -> jwt.PyJWK | None:
        response: httpx.Response = _telegram_login_client.get(self.JWKS_URL)
        response.raise_for_status()

        keys: list[dict[str, Any]] = response.json()['keys']

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

        if TYPE_CHECKING:
            first_name: str
            last_name: str | None

        first_name, _, last_name = cast(str, claims['name']).partition(' ')
        last_name = last_name or None

        user, created = User.objects.update_or_create(
            telegram_id=telegram_id,
            defaults={'first_name': first_name, 'last_name': last_name},
        )

        if not self.user_can_authenticate(user):
            return None

        return user
