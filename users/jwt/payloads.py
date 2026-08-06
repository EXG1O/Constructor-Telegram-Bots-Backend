from django.utils import timezone

from ..enums import TokenType

from calendar import timegm
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Any, Self
from uuid import uuid4

if TYPE_CHECKING:
    from .tokens import BaseToken, RefreshToken


@dataclass
class TokenPayload:
    jti: str
    typ: TokenType
    sub: str
    exp: int
    iat: int

    @classmethod
    def create(cls, token_cls: BaseToken[Any], sub: str, **kwargs: Any) -> Self:
        current_date: datetime = timezone.now()

        return cls(
            jti=uuid4().hex,
            typ=token_cls._type,
            sub=sub,
            exp=timegm((current_date + token_cls.lifetime).utctimetuple()),
            iat=timegm(current_date.utctimetuple()),
            **kwargs,
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AccessTokenPayload(TokenPayload):
    refresh_jti: str

    @classmethod
    def create(  # type: ignore [override]
        cls, token_cls: BaseToken[Any], refresh_token: RefreshToken
    ) -> Self:
        return super().create(
            token_cls, refresh_token.payload.sub, refresh_jti=refresh_token.payload.jti
        )
