from django.conf import settings

import httpx
import orjson

from .models import InitCheckoutResponse, RefundPayment, ResponseObject
from .types import SendTelegramMessage
from .utils import build_send_telegram_message_payload

from http import HTTPMethod
from types import TracebackType
from typing import Any, Self, Unpack, overload
import logging

logger = logging.getLogger(__name__)


class Client:
    def __init__(self) -> None:
        self._client = httpx.Client(
            base_url=str(settings.PLATFORM_BOT_URL),
            headers={
                'User-Agent': settings.APP_USER_AGENT,
                'X-API-KEY': settings.PLATFORM_BOT_MICROSERVICE_TOKEN,
            },
            transport=httpx.HTTPTransport(
                trust_env=False,
                limits=httpx.Limits(
                    max_connections=6, max_keepalive_connections=1, keepalive_expiry=2
                ),
                uds=(
                    str(settings.PLATFORM_BOT_SOCKET)
                    if settings.PLATFORM_BOT_SOCKET
                    else None
                ),
                retries=2,
            ),
        )

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self._client.close()

    @overload
    def _request[T: ResponseObject](
        self,
        method: HTTPMethod,
        endpoint: str,
        response_model: type[T],
        json: Any | None = None,
    ) -> T: ...

    @overload
    def _request(
        self,
        method: HTTPMethod,
        endpoint: str,
        response_model: None = None,
        json: Any | None = None,
    ) -> None: ...

    def _request[T: ResponseObject](
        self,
        method: HTTPMethod,
        endpoint: str,
        response_model: type[T] | None = None,
        json: Any | None = None,
    ) -> T | None:
        try:
            response: httpx.Response = self._client.request(
                method,
                endpoint,
                headers={'Content-Type': 'application/json'},
                content=orjson.dumps(json) if json is not None else None,
            )
            response.raise_for_status()
        except httpx.HTTPError:
            logger.exception('Failed request to the platform bot microservice.')
            raise
        else:
            if not response_model:
                return None
            return response_model.model_validate_json(response.content)

    def init_checkout(
        self,
        user_id: int,
        title: str,
        description: str,
        period_months: int,
        amount: int,
    ) -> InitCheckoutResponse:
        return self._request(
            HTTPMethod.POST,
            '/init-checkout/',
            json={
                'user_service_id': user_id,
                'title': title,
                'description': description,
                'period_months': period_months,
                'amount': amount,
            },
            response_model=InitCheckoutResponse,
        )

    def refund_payments(self, data: list[RefundPayment]) -> None:
        self._request(
            HTTPMethod.POST,
            '/refund-payments/',
            json=[item.model_dump(by_alias=True) for item in data],
        )

    def send_telegram_message(self, **kwargs: Unpack[SendTelegramMessage]) -> None:
        self._request(
            HTTPMethod.POST,
            '/send-telegram-message/',
            json=build_send_telegram_message_payload(**kwargs),
        )

    def send_telegram_messages(self, data: list[SendTelegramMessage]) -> None:
        self._request(
            HTTPMethod.POST,
            '/send-telegram-messages/',
            json=[build_send_telegram_message_payload(**item) for item in data],
        )
