from django.conf import settings
from django.test import TestCase
from django.utils import timezone

from platform_bot.models import PlatformBot
from users.tests.mixins import UserMixin

from ..enums import InvoiceStatus
from ..models import Subscription, SubscriptionInvoice
from ..tasks import (
    delete_expired_subscriptions,
    make_pending_invoices_expired,
    send_subscription_expiry_notifications,
)

from datetime import timedelta
from unittest.mock import Mock, patch


class MakePendingInvoicesExpiredTaskTests(UserMixin, TestCase):
    def setUp(self) -> None:
        super().setUp()

        self.old_invoice: SubscriptionInvoice = self.user.subscription_invoices.create(
            period_months=1, amount_stars=100
        )
        self.old_invoice.created_date = (
            timezone.now() - settings.PREMIUM_INVOICE_PENDING_TIMEOUT
        )
        self.old_invoice.save(update_fields=['created_date'])

        self.new_invoice: SubscriptionInvoice = self.user.subscription_invoices.create(
            period_months=1, amount_stars=100
        )

    def test_expire_pending_invoice_exceeding_timeout(self) -> None:
        make_pending_invoices_expired.delay()

        self.old_invoice.refresh_from_db()
        self.assertEqual(self.old_invoice.status, InvoiceStatus.EXPIRED)

    def test_skip_pending_invoice_within_timeout(self) -> None:
        make_pending_invoices_expired.delay()

        self.new_invoice.refresh_from_db()
        self.assertEqual(self.new_invoice.status, InvoiceStatus.PENDING)

    def test_skip_non_pending_invoice_exceeding_timeout(self) -> None:
        invoice: SubscriptionInvoice = self.user.subscription_invoices.create(
            status=InvoiceStatus.PAID, period_months=1, amount_stars=100
        )
        invoice.created_date = timezone.now() - settings.PREMIUM_INVOICE_PENDING_TIMEOUT
        invoice.save(update_fields=['created_date'])

        make_pending_invoices_expired.delay()

        invoice.refresh_from_db()
        self.assertEqual(invoice.status, InvoiceStatus.PAID)


class SendSubscriptionExpiryNotificationsTaskTests(UserMixin, TestCase):
    def setUp(self) -> None:
        super().setUp()

        self.patcher_bot_get_client = patch.object(PlatformBot, 'get_client')

        self.mock_bot_client = Mock()

        mock_bot_get_client = self.patcher_bot_get_client.start()
        mock_bot_get_client.return_value.__enter__.return_value = self.mock_bot_client

    def tearDown(self) -> None:
        super().tearDown()
        self.patcher_bot_get_client.stop()

    def test_notify_expiring_subscriptions(self) -> None:
        Subscription.objects.create(
            owner=self.user,
            end_date=(
                timezone.now()
                + (
                    settings.PREMIUM_SUBSCRIPTION_EXPIRY_NOTIFICATION_START
                    - settings.PREMIUM_SUBSCRIPTION_EXPIRY_NOTIFICATION_END
                )
            ),
        )

        send_subscription_expiry_notifications.delay()
        self.assertEqual(
            self.mock_bot_client.send_telegram_messages.call_args.args[0][0].get(
                'chat_ids'
            ),
            [self.user.telegram_id],
        )

    def test_skip_subscriptions_not_expiring_soon(self) -> None:
        Subscription.objects.create(
            owner=self.user,
            end_date=(
                timezone.now()
                + settings.PREMIUM_SUBSCRIPTION_EXPIRY_NOTIFICATION_START * 2
            ),
        )

        send_subscription_expiry_notifications.delay()
        self.mock_bot_client.send_telegram_messages.assert_not_called()

    def test_skip_expired_subscriptions(self) -> None:
        Subscription.objects.create(
            owner=self.user, end_date=timezone.now() - timedelta(days=1)
        )

        send_subscription_expiry_notifications.delay()
        self.mock_bot_client.send_telegram_messages.assert_not_called()


class DeleteExpiredSubscriptionsTaskTests(UserMixin, TestCase):
    def setUp(self) -> None:
        super().setUp()

        self.patcher_bot_get_client = patch.object(PlatformBot, 'get_client')

        self.mock_bot_client = Mock()

        mock_bot_get_client = self.patcher_bot_get_client.start()
        mock_bot_get_client.return_value.__enter__.return_value = self.mock_bot_client

    def tearDown(self) -> None:
        super().tearDown()
        self.patcher_bot_get_client.stop()

    def test_delete_expired_subscriptions(self) -> None:
        subscription: Subscription = Subscription.objects.create(
            owner=self.user, end_date=timezone.now() - timedelta(days=1)
        )

        delete_expired_subscriptions.delay()
        self.assertEqual(
            self.mock_bot_client.send_telegram_message.call_args.kwargs['chat_ids'],
            [self.user.telegram_id],
        )
        self.assertFalse(Subscription.objects.filter(id=subscription.id).exists())

    def test_skip_non_expired_subscriptions(self) -> None:
        subscription: Subscription = Subscription.objects.create(
            owner=self.user, end_date=timezone.now() + timedelta(days=1)
        )

        delete_expired_subscriptions.delay()
        self.mock_bot_client.send_telegram_message.assert_not_called()
        self.assertTrue(Subscription.objects.filter(id=subscription.id).exists())

    def test_skip_when_no_subscriptions(self) -> None:
        delete_expired_subscriptions.delay()
        self.mock_bot_client.send_telegram_message.assert_not_called()
