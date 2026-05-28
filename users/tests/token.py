from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory, force_authenticate

from constructor_telegram_bots.utils.tests import assert_view_basic_protected

from ..models import Token
from ..views import TokenViewSet
from .mixins import UserMixin

from typing import TYPE_CHECKING


class TokenViewSetTests(UserMixin, TestCase):
    list_url: str = reverse('api:users:token-list')

    def setUp(self) -> None:
        super().setUp()

        self.factory = APIRequestFactory()
        self.token: Token = self.user_refresh_token.token

        self.detail_true_url: str = reverse(
            'api:users:token-detail',
            kwargs={'jti': self.token.jti},
        )
        self.detail_false_url: str = reverse(
            'api:users:token-detail', kwargs={'jti': '***'}
        )

    def test_list(self) -> None:
        view = TokenViewSet.as_view({'get': 'list'})

        request: Request = self.factory.get(self.list_url)
        assert_view_basic_protected(view, request, self.user_access_token)

        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        response: Response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve(self) -> None:
        view = TokenViewSet.as_view({'get': 'retrieve'})

        if TYPE_CHECKING:
            request: Request
            response: Response

        request = self.factory.get(self.detail_true_url)
        assert_view_basic_protected(view, request, self.user_access_token)

        request = self.factory.get(self.detail_false_url)
        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        response = view(request, jti='***')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        request = self.factory.get(self.detail_true_url)
        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        response = view(request, jti=self.token.jti)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
