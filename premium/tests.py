from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory, force_authenticate

from constructor_telegram_bots.utils.tests import assert_view_basic_protected
from users.tests.mixins import UserMixin

from .models import Subscription, SubscriptionInvoice, SubscriptionPrice
from .views import (
    SubscriptionInvoiceViewSet,
    SubscriptionPriceViewSet,
    SubscriptionViewSet,
)

from typing import TYPE_CHECKING, Any


class SubscriptionPriceViewSetTests(TestCase):
    url: str = reverse('api:premium:subscription-price-list')

    def setUp(self) -> None:
        self.factory = APIRequestFactory()
        self.subscription_price: SubscriptionPrice = SubscriptionPrice.objects.create(
            period_months=1, amount_stars_per_month=100
        )

    def test_list(self) -> None:
        view = SubscriptionPriceViewSet.as_view({'get': 'list'})
        request: Request = self.factory.get(self.url)
        response: Response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class SubscriptionInvoiceViewSetTests(UserMixin, TestCase):
    list_url: str = reverse('api:premium:subscription-invoice-list')

    def setUp(self) -> None:
        super().setUp()

        self.factory = APIRequestFactory()
        self.invoice: SubscriptionInvoice = self.user.subscription_invoices.create(
            period_months=1, amount_stars=100
        )

        true_kwargs: dict[str, Any] = {'id': self.invoice.id}
        false_kwargs: dict[str, Any] = {'id': 0}

        self.detail_true_url: str = reverse(
            'api:premium:subscription-invoice-detail', kwargs=true_kwargs
        )
        self.detail_false_url: str = reverse(
            'api:premium:subscription-invoice-detail', kwargs=false_kwargs
        )

    def test_list(self) -> None:
        view = SubscriptionInvoiceViewSet.as_view({'get': 'list'})

        if TYPE_CHECKING:
            response: Response

        request: Request = self.factory.get(self.list_url)
        assert_view_basic_protected(view, request, self.user_access_token)

        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve(self) -> None:
        view = SubscriptionInvoiceViewSet.as_view({'get': 'retrieve'})

        if TYPE_CHECKING:
            request: Request
            response: Response

        request = self.factory.get(self.detail_true_url)
        assert_view_basic_protected(
            view, request, self.user_access_token, id=self.invoice.id
        )

        request = self.factory.get(self.detail_false_url)
        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        response = view(request, id=0)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        request = self.factory.get(self.detail_true_url)
        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        response = view(request, id=self.invoice.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class SubscriptionViewSetTests(UserMixin, TestCase):
    url: str = reverse('api:premium:subscription-detail')

    def setUp(self) -> None:
        super().setUp()
        self.factory = APIRequestFactory()
        self.subscription: Subscription = Subscription.objects.create(
            owner=self.user, end_date=timezone.now()
        )

    def test_retrieve(self) -> None:
        view = SubscriptionViewSet.as_view({'get': 'retrieve'})

        if TYPE_CHECKING:
            request: Request
            response: Response

        request = self.factory.get(self.url)
        assert_view_basic_protected(view, request, self.user_access_token)

        request = self.factory.get(self.url)
        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
