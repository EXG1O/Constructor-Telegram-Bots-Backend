from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory, force_authenticate

from constructor_telegram_bots.utils.tests import assert_view_basic_protected
from users.tests.mixins import UserMixin

from ..models import Subscription
from ..views import SubscriptionViewSet

from typing import TYPE_CHECKING


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
