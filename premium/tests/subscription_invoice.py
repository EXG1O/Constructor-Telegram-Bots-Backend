from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory, force_authenticate

from constructor_telegram_bots.utils.tests import assert_view_basic_protected
from users.tests.mixins import UserMixin

from ..models import SubscriptionInvoice
from ..views import SubscriptionInvoiceViewSet

from typing import Any


class SubscriptionInvoiceViewSetTests(UserMixin, TestCase):
    def setUp(self) -> None:
        super().setUp()

        self.factory = APIRequestFactory()
        self.invoice: SubscriptionInvoice = self.user.subscription_invoices.create(
            period_months=1, amount_stars=100
        )

        self.detail_url_kwargs: dict[str, Any] = {'id': self.invoice.id}

        self.list_url: str = reverse('api:premium:subscription-invoice-list')
        self.detail_url: str = reverse(
            'api:premium:subscription-invoice-detail', kwargs=self.detail_url_kwargs
        )

    def test_invalid_id(self) -> None:
        view = SubscriptionInvoiceViewSet.as_view({'get': 'retrieve'})

        request: Request = self.factory.get(self.detail_url)

        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        view_kwargs: dict[str, Any] = self.detail_url_kwargs.copy()
        view_kwargs['id'] = 0

        response: Response = view(request, **view_kwargs)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_list(self) -> None:
        view = SubscriptionInvoiceViewSet.as_view({'get': 'list'})

        request: Request = self.factory.get(self.list_url)
        assert_view_basic_protected(view, request, self.user_access_token)

        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        response: Response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve(self) -> None:
        view = SubscriptionInvoiceViewSet.as_view({'get': 'retrieve'})

        request: Request = self.factory.get(self.detail_url)
        assert_view_basic_protected(
            view, request, self.user_access_token, **self.detail_url_kwargs
        )

        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        response: Response = view(request, **self.detail_url_kwargs)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
