from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory, force_authenticate

from constructor_telegram_bots.utils.tests import assert_view_basic_protected
from users.tests.mixins import UserMixin
from users.utils.tests import assert_view_requires_terms_acceptance

from ..models import SubscriptionPrice
from ..views import SubscriptionPriceViewSet

from typing import Any
from unittest.mock import patch


class SubscriptionPriceViewSetTests(UserMixin, TestCase):
    def setUp(self) -> None:
        super().setUp()

        self.factory = APIRequestFactory()
        self.price: SubscriptionPrice = SubscriptionPrice.objects.create(
            period_months=1, amount_stars_per_month=100
        )

        self.detail_url_kwargs: dict[str, Any] = {'id': self.price.id}

        self.list_url: str = reverse('api:premium:subscription-price-list')
        self.detail_url: str = reverse(
            'api:premium:subscription-price-detail', kwargs=self.detail_url_kwargs
        )

    def test_invalid_id(self) -> None:
        view = SubscriptionPriceViewSet.as_view({'get': 'retrieve'})

        request: Request = self.factory.get(self.detail_url)

        view_kwargs: dict[str, Any] = self.detail_url_kwargs.copy()
        view_kwargs['id'] = 0

        response: Response = view(request, **view_kwargs)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_list(self) -> None:
        view = SubscriptionPriceViewSet.as_view({'get': 'list'})
        request: Request = self.factory.get(self.list_url)
        response: Response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve(self) -> None:
        view = SubscriptionPriceViewSet.as_view({'get': 'retrieve'})
        request: Request = self.factory.get(self.detail_url)
        response: Response = view(request, **self.detail_url_kwargs)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_checkout(self) -> None:
        view = SubscriptionPriceViewSet.as_view(
            {'get': 'checkout'}, **SubscriptionPriceViewSet.checkout.kwargs
        )

        checkout_url_kwargs: dict[str, Any] = self.detail_url_kwargs.copy()

        request: Request = self.factory.get(
            reverse(
                'api:premium:subscription-price-checkout', kwargs=checkout_url_kwargs
            )
        )
        assert_view_basic_protected(
            view, request, self.user_access_token, **checkout_url_kwargs
        )
        assert_view_requires_terms_acceptance(
            view, request, self.user, **checkout_url_kwargs
        )

        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        with patch.object(
            SubscriptionPrice, 'get_checkout_url'
        ) as mock_get_checkout_url:
            mock_get_checkout_url.return_value = 'https://example.com'
            response: Response = view(request, **checkout_url_kwargs)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_get_checkout_url.assert_called_once()
