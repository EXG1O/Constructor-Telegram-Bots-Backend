from requests_unixsocket import Session
from yarl import URL

from ...models import Trigger
from ..serializers import TriggerSerializer

from requests import Response

from http import HTTPMethod
from typing import Any

_session: Session = Session()


class ServiceClient:
    def __init__(self, url: str, access_token: str) -> None:
        self.url = URL(url)
        self.headers = {'X-API-KEY': access_token}

    def _request(
        self, method: HTTPMethod, endpoint: str, data: Any | None = None
    ) -> Response:
        response: Response = _session.request(
            method, str(self.url / endpoint), headers=self.headers, json=data
        )
        response.raise_for_status()
        return response

    def get_bot_ids(self) -> list[int]:
        response: Response = self._request(HTTPMethod.GET, 'bots/')
        return response.json()

    def start_bot(self, bot_id: int, bot_token: str) -> Response:
        return self._request(
            HTTPMethod.POST, f'bots/{bot_id}/start/', data={'bot_token': bot_token}
        )

    def restart_bot(self, bot_id: int) -> Response:
        return self._request(HTTPMethod.POST, f'bots/{bot_id}/restart/')

    def stop_bot(self, bot_id: int) -> Response:
        return self._request(HTTPMethod.POST, f'bots/{bot_id}/stop/')

    def send_trigger(
        self, bot_id: int, trigger: Trigger, payload: Any | None = None
    ) -> Response:
        return self._request(
            HTTPMethod.POST,
            f'bots/{bot_id}/webhooks/trigger/',
            data={'trigger': TriggerSerializer(trigger).data, 'payload': payload},
        )
