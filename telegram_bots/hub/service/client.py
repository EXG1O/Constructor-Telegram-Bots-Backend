from django.conf import settings

import httpx

from ...models import Trigger
from ..serializers import TriggerSerializer
from .schemas import BotCredentials

from http import HTTPMethod
from types import TracebackType
from typing import Any, Self


class ServiceClient:
    def __init__(self, container_id: str, access_token: str) -> None:
        self._client = httpx.Client(
            base_url='http://localhost',
            headers={'User-Agent': settings.APP_USER_AGENT, 'X-API-KEY': access_token},
            transport=httpx.HTTPTransport(
                trust_env=False,
                limits=httpx.Limits(
                    max_connections=6, max_keepalive_connections=1, keepalive_expiry=2
                ),
                uds=str(settings.SOCKETS_DIR / f'{container_id[:12]}.sock'),
                retries=3,
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

    def _request(
        self,
        method: HTTPMethod,
        endpoint: str,
        content: str | bytes | None = None,
        json: Any | None = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        response: httpx.Response = self._client.request(
            method, endpoint, headers=headers, content=content, json=json
        )
        response.raise_for_status()
        return response

    def get_bot_ids(self) -> list[int]:
        return self._request(HTTPMethod.GET, '/bots/').json()

    def start_bots(self, bots: list[BotCredentials]) -> None:
        self._request(HTTPMethod.POST, '/bots/start/', json=bots)

    def start_bot(self, id: int, token: str, webhook_url: str) -> None:
        self._request(
            HTTPMethod.POST,
            f'/bots/{id}/start/',
            json={'token': token, 'webhook_url': webhook_url},
        )

    def restart_bot(self, id: int, token: str, webhook_url: str) -> None:
        self._request(
            HTTPMethod.POST,
            f'/bots/{id}/restart/',
            json={'token': token, 'webhook_url': webhook_url},
        )

    def stop_bot(self, id: int) -> None:
        self._request(HTTPMethod.POST, f'/bots/{id}/stop/')

    def forward_telegram_data(self, bot_id: int, data: Any) -> None:
        self._request(
            HTTPMethod.POST,
            f'bots/{bot_id}/webhooks/telegram/',
            headers={'Content-Type': 'application/json'},
            content=data,
        )

    def send_trigger(
        self,
        bot_id: int,
        trigger: Trigger,
        trigger_has_target_connections: bool,
        payload: str,
    ) -> None:
        self._request(
            HTTPMethod.POST,
            f'/bots/{bot_id}/webhooks/trigger/',
            json={
                'trigger': TriggerSerializer(trigger).data,
                'trigger_has_target_connections': trigger_has_target_connections,
                'payload': payload,
            },
        )
