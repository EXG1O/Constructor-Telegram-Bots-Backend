from django.conf import settings

from httpcore import ConnectError, ConnectionPool, Response

from ...models import Trigger
from ..serializers import TriggerSerializer
from .exceptions import HTTPError
from .schemas import BotCredentials

from http import HTTPMethod, HTTPStatus
from typing import Any
import json
import time


class ServiceClient:
    def __init__(self, container_id: str, access_token: str) -> None:
        self.pool = ConnectionPool(
            uds=str(settings.SOCKETS_DIR / f'{container_id[:12]}.sock')
        )
        self.headers: dict[str | bytes, str | bytes] = {
            'X-API-KEY': access_token,
            'Content-Type': 'application/json',
        }

    def _request(
        self,
        method: HTTPMethod,
        endpoint: str,
        data: list[Any] | dict[str, Any] | bytes | None = None,
    ) -> Response:
        max_retries: int = 3
        backoff_delay: float = 0.5

        for attempt in range(max_retries + 1):
            try:
                response: Response = self.pool.request(
                    method,
                    f'http://localhost/{endpoint}',
                    headers=self.headers,
                    content=(
                        data
                        if isinstance(data, bytes | None)
                        else json.dumps(data, ensure_ascii=False).encode()
                    ),
                    extensions={'timeout': {'connect': 4.0, 'pool': 8.0}},
                )

                if response.status >= 400:
                    raise HTTPError(response)  # noqa: TRY301
            except (ConnectError, TimeoutError, HTTPError) as error:
                if attempt >= max_retries:
                    raise error

                if isinstance(error, HTTPError) and error.response.status not in [
                    HTTPStatus.SERVICE_UNAVAILABLE,
                    HTTPStatus.BAD_GATEWAY,
                ]:
                    raise error

                time.sleep(backoff_delay * (2**attempt))
            else:
                return response

        raise RuntimeError(
            'Request loop exited unexpectedly without returning a response '
            'or raising an error.'
        )

    def get_bot_ids(self) -> list[int]:
        response: Response = self._request(HTTPMethod.GET, 'bots/')
        return json.loads(response.content)

    def start_bots(self, bots: list[BotCredentials]) -> Response:
        return self._request(HTTPMethod.POST, 'bots/start/', data=bots)

    def start_bot(self, id: int, token: str, webhook_url: str) -> Response:
        return self._request(
            HTTPMethod.POST,
            f'bots/{id}/start/',
            data={'token': token, 'webhook_url': webhook_url},
        )

    def restart_bot(self, id: int, token: str, webhook_url: str) -> Response:
        return self._request(
            HTTPMethod.POST,
            f'bots/{id}/restart/',
            data={'token': token, 'webhook_url': webhook_url},
        )

    def stop_bot(self, id: int) -> Response:
        return self._request(HTTPMethod.POST, f'bots/{id}/stop/')

    def forward_telegram_data(self, bot_id: int, data: Any) -> Response:
        return self._request(
            HTTPMethod.POST, f'bots/{bot_id}/webhooks/telegram/', data=data
        )

    def send_trigger(
        self, bot_id: int, trigger: Trigger, payload: Any | None = None
    ) -> Response:
        return self._request(
            HTTPMethod.POST,
            f'bots/{bot_id}/webhooks/trigger/',
            data={'trigger': TriggerSerializer(trigger).data, 'payload': payload},
        )
