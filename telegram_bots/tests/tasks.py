from django.test import TestCase

from users.tests.mixins import UserMixin

from ..hub.models import TelegramBotsHub
from ..hub.tests.mixins import HubMixin
from ..models import TelegramBot
from ..tasks import (
    migrate_telegram_bots,
    restart_telegram_bot,
    start_telegram_bot,
    stop_telegram_bot,
)
from .mixins import TelegramBotMixin

from unittest.mock import MagicMock, call, patch


class StartTelegramBotTaskTestCase(HubMixin, TelegramBotMixin, UserMixin, TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.telegram_bot.is_loading = True
        self.telegram_bot.save(update_fields=['is_loading'])

    def test_start_bot(self) -> None:
        start_telegram_bot.delay(
            id=self.telegram_bot.id,
            token=self.telegram_bot.api_token,
            webhook_url=self.telegram_bot.webhook_url,
            is_premium=False,
        )
        self.mock_hub_client.start_bot.assert_called_once_with(
            self.telegram_bot.id,
            token=self.telegram_bot.api_token,
            webhook_url=self.telegram_bot.webhook_url,
        )

    def test_reset_bot_loading_on_error(self) -> None:
        self.mock_hub_client.start_bot.side_effect = RuntimeError

        with self.assertRaises(RuntimeError):
            start_telegram_bot.delay(
                id=self.telegram_bot.id,
                token=self.telegram_bot.api_token,
                webhook_url=self.telegram_bot.webhook_url,
                is_premium=False,
            )

        self.telegram_bot.refresh_from_db()
        self.assertFalse(self.telegram_bot.is_loading)


class RestartTelegramBotTaskTestCase(HubMixin, TelegramBotMixin, UserMixin, TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.telegram_bot.hub = self.hub
        self.telegram_bot.is_loading = True
        self.telegram_bot.save(update_fields=['hub', 'is_loading'])

    def test_restart_bot(self) -> None:
        restart_telegram_bot.delay(
            id=self.telegram_bot.id,
            token=self.telegram_bot.api_token,
            webhook_url=self.telegram_bot.webhook_url,
        )
        self.mock_hub_client.restart_bot.assert_called_once_with(
            self.telegram_bot.id,
            token=self.telegram_bot.api_token,
            webhook_url=self.telegram_bot.webhook_url,
        )

    def test_reset_bot_loading_on_error(self) -> None:
        self.mock_hub_client.restart_bot.side_effect = RuntimeError

        with self.assertRaises(RuntimeError):
            restart_telegram_bot.delay(
                id=self.telegram_bot.id,
                token=self.telegram_bot.api_token,
                webhook_url=self.telegram_bot.webhook_url,
            )

        self.telegram_bot.refresh_from_db()
        self.assertFalse(self.telegram_bot.is_loading)


class StopTelegramBotTaskTestCase(HubMixin, TelegramBotMixin, UserMixin, TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.telegram_bot.hub = self.hub
        self.telegram_bot.is_loading = True
        self.telegram_bot.save(update_fields=['hub', 'is_loading'])

    def test_stop_bot(self) -> None:
        stop_telegram_bot.delay(id=self.telegram_bot.id)
        self.mock_hub_client.stop_bot.assert_called_once_with(self.telegram_bot.id)

    def test_reset_bot_loading_on_error(self) -> None:
        self.mock_hub_client.stop_bot.side_effect = RuntimeError

        with self.assertRaises(RuntimeError):
            stop_telegram_bot.delay(id=self.telegram_bot.id)

        self.telegram_bot.refresh_from_db()
        self.assertFalse(self.telegram_bot.is_loading)


class MigrateTelegramBotsTaskTestCase(UserMixin, TestCase):
    def setUp(self) -> None:
        super().setUp()

        self.default_hub: TelegramBotsHub = TelegramBotsHub.objects.create(
            container_id='default_container'
        )
        self.premium_hub: TelegramBotsHub = TelegramBotsHub.objects.create(
            container_id='premium_container', is_premium=True
        )

        self.hub_clients: dict[int, MagicMock] = {}

        for hub in (self.default_hub, self.premium_hub):
            client = MagicMock()
            client.__enter__.return_value = client
            client.get_bot_ids.return_value = []
            self.hub_clients[hub.id] = client

        self.patcher_hub_get_client = patch.object(
            TelegramBotsHub,
            'get_client',
            autospec=True,
            side_effect=lambda hub: self.hub_clients[hub.id],
        )
        self.mock_hub_get_client = self.patcher_hub_get_client.start()

    def tearDown(self) -> None:
        super().tearDown()
        self.patcher_hub_get_client.stop()

    def test_migrate_multiple_bots_to_premium_hub(self) -> None:
        bots: list[TelegramBot] = [
            self.user.telegram_bots.create(
                api_token=f'{index}:token', hub=self.default_hub
            )
            for index in range(3)
        ]

        migrate_telegram_bots.delay(owner_id=self.user.id, target_hub_is_premium=True)

        default_hub_client: MagicMock = self.hub_clients[self.default_hub.id]

        self.assertEqual(default_hub_client.stop_bot.call_count, len(bots))
        default_hub_client.stop_bot.assert_has_calls(
            [call(bot.id) for bot in bots], any_order=True
        )

        premium_hub_client: MagicMock = self.hub_clients[self.premium_hub.id]

        self.assertEqual(premium_hub_client.start_bot.call_count, len(bots))
        premium_hub_client.start_bot.assert_has_calls(
            [
                call(bot.id, token=bot.api_token, webhook_url=bot.webhook_url)
                for bot in bots
            ],
            any_order=True,
        )

    def test_migrate_only_premium_bots_to_default_hub(self) -> None:
        bots: list[TelegramBot] = [
            self.user.telegram_bots.create(
                api_token=f'{index}:token', hub=self.premium_hub
            )
            for index in range(2)
        ]
        self.user.telegram_bots.create(
            api_token='we appreciate every one of you!', hub=self.default_hub
        )

        migrate_telegram_bots.delay(owner_id=self.user.id, target_hub_is_premium=False)

        premium_hub_client: MagicMock = self.hub_clients[self.premium_hub.id]

        self.assertEqual(premium_hub_client.stop_bot.call_count, len(bots))
        premium_hub_client.stop_bot.assert_has_calls(
            [call(bot.id) for bot in bots], any_order=True
        )

        default_hub_client: MagicMock = self.hub_clients[self.default_hub.id]

        self.assertEqual(default_hub_client.start_bot.call_count, len(bots))
        default_hub_client.start_bot.assert_has_calls(
            [
                call(bot.id, token=bot.api_token, webhook_url=bot.webhook_url)
                for bot in bots
            ],
            any_order=True,
        )
        default_hub_client.stop_bot.assert_not_called()

    def test_migrate_only_default_bots_to_premium_hub(self) -> None:
        bots: list[TelegramBot] = [
            self.user.telegram_bots.create(
                api_token=f'{index}:token', hub=self.default_hub
            )
            for index in range(2)
        ]
        self.user.telegram_bots.create(api_token='just text, lol', hub=self.premium_hub)

        migrate_telegram_bots.delay(owner_id=self.user.id, target_hub_is_premium=True)

        default_client: MagicMock = self.hub_clients[self.default_hub.id]

        self.assertEqual(default_client.stop_bot.call_count, len(bots))
        default_client.stop_bot.assert_has_calls(
            [call(bot.id) for bot in bots], any_order=True
        )

        premium_client: MagicMock = self.hub_clients[self.premium_hub.id]

        self.assertEqual(premium_client.start_bot.call_count, len(bots))
        premium_client.start_bot.assert_has_calls(
            [
                call(bot.id, token=bot.api_token, webhook_url=bot.webhook_url)
                for bot in bots
            ],
            any_order=True,
        )
        premium_client.stop_bot.assert_not_called()

    def test_skip_migration_without_bots(self) -> None:
        migrate_telegram_bots.delay(owner_id=self.user.id, target_hub_is_premium=True)
        self.mock_hub_get_client.assert_not_called()
