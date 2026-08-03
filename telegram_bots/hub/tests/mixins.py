from docker import DockerClient
from docker.models.containers import Container

from ...models import TelegramBot
from ..models import TelegramBotsHub

from typing import TYPE_CHECKING
from unittest.mock import Mock, patch


class HubMixin:
    if TYPE_CHECKING:
        telegram_bot: TelegramBot

    def setUp(self) -> None:
        super().setUp()  # type: ignore [misc]

        self.patcher_docker_containers = patch.object(DockerClient, 'containers')
        self.patcher_hub_get_client = patch.object(TelegramBotsHub, 'get_client')

        self.mock_docker_containers = self.patcher_docker_containers.start()
        self.mock_docker_containers.run.return_value = Container(
            attrs={Container.id_attribute: 'random_id'}
        )

        self.mock_hub_client = Mock()

        mock_hub_get_client = self.patcher_hub_get_client.start()
        mock_hub_get_client.return_value.__enter__.return_value = self.mock_hub_client

        self.hub: TelegramBotsHub = TelegramBotsHub.objects.create(container_id='I<3U')

    def tearDown(self) -> None:
        super().tearDown()  # type: ignore [misc]
        self.patcher_docker_containers.stop()
        self.patcher_hub_get_client.stop()
