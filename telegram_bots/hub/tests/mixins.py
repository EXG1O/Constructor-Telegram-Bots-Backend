from ..models import TelegramBotsHub


class HubMixin:
    def setUp(self) -> None:
        super().setUp()  # type: ignore [misc]
        self.hub: TelegramBotsHub = TelegramBotsHub.objects.create(
            url='http://127.0.0.1'
        )
