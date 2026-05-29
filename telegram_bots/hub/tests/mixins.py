from ...models import TelegramBot
from ..models import TelegramBotsHub

from typing import TYPE_CHECKING
from unittest.mock import patch


class HubMixin:
    if TYPE_CHECKING:
        telegram_bot: TelegramBot

    def setUp(self) -> None:
        super().setUp()  # type: ignore [misc]

        self.patcher_hub_client = patch.object(TelegramBotsHub, 'client')
        self.mock_hub_client = self.patcher_hub_client.start()
        self.mock_hub_client.get_bot_ids.return_value = []

        self.hub: TelegramBotsHub = TelegramBotsHub.objects.create(
            url='http://127.0.0.1'
        )

    def tearDown(self) -> None:
        super().tearDown()  # type: ignore [misc]
        self.patcher_hub_client.stop()
