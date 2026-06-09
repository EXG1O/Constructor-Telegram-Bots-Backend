from django.conf import settings
from django.test import TestCase
from django.utils import timezone

from telegram_bots.hub.tasks import ensure_idle_telegram_bots_hubs
from telegram_bots.hub.tests.mixins import HubMixin
from telegram_bots.tests.mixins import TelegramBotMixin
from users.tests.mixins import UserMixin

from datetime import timedelta
from unittest.mock import patch


class EnsureIdleTelegramBotsHubsTaskTests(
    HubMixin, TelegramBotMixin, UserMixin, TestCase
):
    def setUp(self) -> None:
        super().setUp()

        self.current_datetime = timezone.now() + timedelta(
            seconds=int(
                settings.CELERY_BEAT_SCHEDULE[
                    'ensure_idle_telegram_bots_hubs_schedule'
                ]['schedule']
            )
        )
        self.patcher_timezone = patch(
            'telegram_bots.hub.tasks.timezone.now', return_value=self.current_datetime
        )
        self.patcher_timezone.start()

    def tearDown(self) -> None:
        super().tearDown()
        self.patcher_timezone.stop()

    def test_sets_idle_start_date_for_empty_hub(self) -> None:
        self.hub.idle_start_date = None
        self.hub.save(update_fields=['idle_start_date'])

        ensure_idle_telegram_bots_hubs()

        self.hub.refresh_from_db()
        self.assertEqual(self.hub.idle_start_date, self.current_datetime)

    def test_does_not_set_idle_start_date_for_hub_with_bots(self) -> None:
        self.hub.idle_start_date = None
        self.hub.save(update_fields=['idle_start_date'])

        self.telegram_bot.hub = self.hub
        self.telegram_bot.must_be_enabled = True
        self.telegram_bot.save(update_fields=['hub', 'must_be_enabled'])

        ensure_idle_telegram_bots_hubs()

        self.hub.refresh_from_db()
        self.assertIsNone(self.hub.idle_start_date)

    def test_does_not_override_existing_idle_start_date(self) -> None:
        existing_date = timezone.now() - timedelta(days=1)
        self.hub.idle_start_date = existing_date
        self.hub.save(update_fields=['idle_start_date'])

        ensure_idle_telegram_bots_hubs()

        self.hub.refresh_from_db()
        self.assertEqual(self.hub.idle_start_date, existing_date)
