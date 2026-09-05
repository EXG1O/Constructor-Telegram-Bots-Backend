from django.conf import settings
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory, force_authenticate

from constructor_telegram_bots.utils.tests import assert_view_basic_protected
from premium.enums import InvoiceStatus
from premium.models import SubscriptionInvoice
from users.tests.mixins import UserMixin

from ..enums import InvoiceType
from ..models import PlatformBot
from ..views import InvoiceViewSet

from contextlib import suppress
from typing import Any


class PremiumInvoiceViewSetTests(UserMixin, TestCase):
    def setUp(self) -> None:
        super().setUp()

        self.factory = APIRequestFactory()
        self.invoice: SubscriptionInvoice = self.user.subscription_invoices.create(
            period_months=1, amount_stars=100
        )

        self.list_url_kwargs: dict[str, Any] = {
            'user_id': self.user.id,
            'invoice_type': InvoiceType.PREMIUM,
        }
        self.detail_url_kwargs: dict[str, Any] = {
            **self.list_url_kwargs,
            'id': self.invoice.id,
        }

        self.list_url: str = reverse(
            'api:platform-bot:invoice-list', kwargs=self.list_url_kwargs
        )
        self.detail_url: str = reverse(
            'api:platform-bot:invoice-detail', kwargs=self.detail_url_kwargs
        )

    def test_invalid_user_id(self) -> None:
        view = InvoiceViewSet.as_view({'get': 'list'})

        request: Request = self.factory.get(self.list_url)

        force_authenticate(request, PlatformBot(), settings.PLATFORM_BOT_SERVICE_TOKEN)  # type: ignore [arg-type]

        view_kwargs: dict[str, Any] = self.list_url_kwargs.copy()
        view_kwargs['user_id'] = 0

        response: Response = view(request, **view_kwargs)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_invalid_invoice_type(self) -> None:
        view = InvoiceViewSet.as_view({'get': 'list'})

        request: Request = self.factory.get(self.list_url)

        force_authenticate(request, PlatformBot(), settings.PLATFORM_BOT_SERVICE_TOKEN)  # type: ignore [arg-type]

        view_kwargs: dict[str, Any] = self.list_url_kwargs.copy()
        view_kwargs['invoice_type'] = 'invalid'

        response: Response = view(request, **view_kwargs)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_invalid_id(self) -> None:
        view = InvoiceViewSet.as_view({'get': 'retrieve'})

        request: Request = self.factory.get(self.detail_url)

        force_authenticate(request, PlatformBot(), settings.PLATFORM_BOT_SERVICE_TOKEN)  # type: ignore [arg-type]

        view_kwargs: dict[str, Any] = self.detail_url_kwargs.copy()
        view_kwargs['id'] = 0

        response: Response = view(request, **view_kwargs)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_list(self) -> None:
        view = InvoiceViewSet.as_view({'get': 'list'})

        request: Request = self.factory.get(self.list_url)
        assert_view_basic_protected(
            view, request, settings.PLATFORM_BOT_SERVICE_TOKEN, **self.list_url_kwargs
        )

        force_authenticate(request, PlatformBot(), settings.PLATFORM_BOT_SERVICE_TOKEN)  # type: ignore [arg-type]

        response: Response = view(request, **self.list_url_kwargs)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve(self) -> None:
        view = InvoiceViewSet.as_view({'get': 'retrieve'})

        request: Request = self.factory.get(self.detail_url)
        assert_view_basic_protected(
            view, request, settings.PLATFORM_BOT_SERVICE_TOKEN, **self.detail_url_kwargs
        )

        force_authenticate(request, PlatformBot(), settings.PLATFORM_BOT_SERVICE_TOKEN)  # type: ignore [arg-type]

        response: Response = view(request, **self.detail_url_kwargs)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create(self) -> None:
        view = InvoiceViewSet.as_view({'post': 'create'})

        period_months: int = 3
        amount_stars: int = 300

        request: Request = self.factory.post(
            self.list_url,
            {'period_months': period_months, 'amount_stars': amount_stars},
            format='json',
        )
        assert_view_basic_protected(
            view, request, settings.PLATFORM_BOT_SERVICE_TOKEN, **self.list_url_kwargs
        )

        force_authenticate(request, PlatformBot(), settings.PLATFORM_BOT_SERVICE_TOKEN)  # type: ignore [arg-type]

        response: Response = view(request, **self.list_url_kwargs)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        new_invoice: SubscriptionInvoice = SubscriptionInvoice.objects.get(
            id=response.data['id']
        )
        self.assertEqual(new_invoice.user, self.user)
        self.assertEqual(new_invoice.period_months, period_months)
        self.assertEqual(new_invoice.amount_stars, amount_stars)

    def test_update_status_pending_to_paid_without_telegram_charge_id(self) -> None:
        view = InvoiceViewSet.as_view({'patch': 'partial_update'})

        request: Request = self.factory.patch(
            self.detail_url, {'status': InvoiceStatus.PAID}, format='json'
        )
        assert_view_basic_protected(
            view, request, settings.PLATFORM_BOT_SERVICE_TOKEN, **self.detail_url_kwargs
        )

        force_authenticate(request, PlatformBot(), settings.PLATFORM_BOT_SERVICE_TOKEN)  # type: ignore [arg-type]

        response: Response = view(request, **self.detail_url_kwargs)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_status_pending_to_paid(self) -> None:
        view = InvoiceViewSet.as_view({'patch': 'partial_update'})

        telegram_charge_id: str = 'tg_charge_123'

        request: Request = self.factory.patch(
            self.detail_url,
            {'status': InvoiceStatus.PAID, 'telegram_charge_id': telegram_charge_id},
            format='json',
        )
        assert_view_basic_protected(
            view, request, settings.PLATFORM_BOT_SERVICE_TOKEN, **self.detail_url_kwargs
        )

        force_authenticate(request, PlatformBot(), settings.PLATFORM_BOT_SERVICE_TOKEN)  # type: ignore [arg-type]

        response: Response = view(request, **self.detail_url_kwargs)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.invoice.refresh_from_db()
        self.assertTrue(self.invoice.subscription)
        self.assertEqual(self.invoice.status, InvoiceStatus.PAID)
        self.assertEqual(self.invoice.telegram_charge_id, telegram_charge_id)

    def test_destroy(self) -> None:
        view = InvoiceViewSet.as_view({'delete': 'destroy'})

        request: Request = self.factory.delete(self.detail_url)
        assert_view_basic_protected(
            view, request, settings.PLATFORM_BOT_SERVICE_TOKEN, **self.detail_url_kwargs
        )

        force_authenticate(request, PlatformBot(), settings.PLATFORM_BOT_SERVICE_TOKEN)  # type: ignore [arg-type]

        response: Response = view(request, **self.detail_url_kwargs)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        with suppress(SubscriptionInvoice.DoesNotExist):
            self.invoice.refresh_from_db()
            raise self.failureException('Invoice has not been deleted from database.')
