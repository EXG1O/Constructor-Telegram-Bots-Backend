from django.contrib.auth import login, logout
from django.http import HttpRequest
from django.utils.translation import gettext as _

from rest_framework.exceptions import APIException

from jwt import PyJWTError

from ..enums import TokenType
from ..jwt.tokens import AccessToken, RefreshToken
from ..models import BlacklistedToken, Token, User


def authenticate_token[JWT: (RefreshToken, AccessToken)](
    raw_token: str, token_cls: type[JWT], exception_cls: type[APIException]
) -> tuple[User, JWT]:
    try:
        token = token_cls(token=raw_token)
    except PyJWTError as error:
        raise exception_cls(_('Недействительный токен.')) from error

    if token.is_blacklisted:
        raise exception_cls(_('Токен в чёрном списке.'))

    user: User | None = token.user

    if not user or not user.is_active:
        raise exception_cls(_('Пользователь неактивен или удалён.'))

    return user, token


def user_login(request: HttpRequest, user: User) -> RefreshToken:
    login(request, user)
    return RefreshToken.for_user(user)


def user_logout(request: HttpRequest, jwt_token: RefreshToken | AccessToken) -> None:
    logout(request)

    if isinstance(jwt_token, RefreshToken):
        jwt_token.to_blacklist()
        return

    token: Token = Token.objects.get(
        jti=jwt_token.payload.refresh_jti, type=TokenType.REFRESH
    )
    BlacklistedToken.objects.create(token=token)


def user_logout_all(request: HttpRequest, user: User) -> None:
    logout(request)
    BlacklistedToken.objects.bulk_create(
        BlacklistedToken(token=token)
        for token in Token.objects.filter(user=user).exclude(blacklisted__isnull=False)
    )
