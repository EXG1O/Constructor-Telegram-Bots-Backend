from django.conf import settings
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory, force_authenticate

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
import httpcore
import jwt

from constructor_telegram_bots.utils.tests import assert_view_basic_protected
from users.tests.mixins import UserMixin

from ..backends import TelegramBackend
from ..jwt.tokens import RefreshToken
from ..models import User
from ..views import UserViewSet

from contextlib import suppress
from datetime import datetime, timedelta
from http import HTTPMethod
from importlib import import_module
from typing import TYPE_CHECKING, Any
from unittest.mock import patch
import base64
import json
import math

SessionStore = import_module(settings.SESSION_ENGINE).SessionStore


class UserViewSetTests(UserMixin, TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.factory = APIRequestFactory()

    def test_retrieve(self) -> None:
        view = UserViewSet.as_view({'get': 'retrieve'})

        if TYPE_CHECKING:
            response: Response

        request: Request = self.factory.get(reverse('api:users:user-detail'))
        assert_view_basic_protected(view, request, self.user_access_token)

        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_login(self) -> None:
        login_init_view = UserViewSet.as_view({'post': 'login_init'})
        login_view = UserViewSet.as_view({'post': 'login'})

        if TYPE_CHECKING:
            request: Request
            response: Response

        init_request = self.factory.post(reverse('api:users:user-login-init'))
        init_request.session = SessionStore()
        force_authenticate(init_request, self.user, None)

        init_response = login_init_view(init_request)
        self.assertEqual(init_response.status_code, status.HTTP_200_OK)
        self.assertIn('code_challenge', init_response.data)

        request = self.factory.post(
            reverse('api:users:user-login'),
            data={'code': 'valid_code', 'redirect_uri': 'http://localhost'},
            format='json',
        )
        request.session = init_request.session
        force_authenticate(request, self.user, None)

        private_key: rsa.RSAPrivateKey = rsa.generate_private_key(
            public_exponent=65537, key_size=2048
        )
        public_key: rsa.RSAPublicKey = private_key.public_key()

        private_pem: bytes = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )

        jwk_key_id: str = 'test-key-id'

        current_datetime: datetime = timezone.now()
        id_token: str = jwt.encode(
            {
                'iss': TelegramBackend.ISSUER,
                'aud': str(settings.TELEGRAM_LOGIN_CLIENT_ID),
                'sub': str(self.user.telegram_id),
                'iat': int(current_datetime.timestamp()),
                'exp': int((current_datetime + timedelta(seconds=30)).timestamp()),
                'id': self.user.telegram_id,
                'name': self.user.full_name,
            },
            private_pem,
            algorithm='RS256',
            headers={'kid': jwk_key_id},
        )

        public_numbers: rsa.RSAPublicNumbers = public_key.public_numbers()
        n_bytes: bytes = public_numbers.n.to_bytes(
            math.ceil(public_numbers.n.bit_length() / 8), byteorder='big'
        )
        e_bytes: bytes = public_numbers.e.to_bytes(
            math.ceil(public_numbers.e.bit_length() / 8), byteorder='big'
        )
        jwk_payload: dict[str, str] = {
            'kty': 'RSA',
            'alg': 'RS256',
            'kid': jwk_key_id,
            'n': base64.urlsafe_b64encode(n_bytes).decode().rstrip('='),
            'e': base64.urlsafe_b64encode(e_bytes).decode().rstrip('='),
            'use': 'sig',
        }

        with patch('users.backends.TELEGRAM_LOGIN_HTTP_POOL') as mock_pool:

            def mock_request(
                method: HTTPMethod, url: str, **kwargs: Any
            ) -> httpcore.Response:
                if url == TelegramBackend.TOKEN_URL:
                    response = httpcore.Response(
                        status=200, content=json.dumps({'id_token': id_token}).encode()
                    )
                elif url == TelegramBackend.JWKS_URL:
                    response = httpcore.Response(
                        status=200, content=json.dumps({'keys': [jwk_payload]}).encode()
                    )
                else:
                    response = httpcore.Response(status=500, content=b'')

                response.read()
                return response

            mock_pool.request = mock_request

            response = login_view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access_token', response.data)
        self.assertIn('refresh_token', response.data)

    def test_logout(self) -> None:
        view = UserViewSet.as_view({'post': 'logout'})

        if TYPE_CHECKING:
            response: Response

        request: Request = self.factory.post(reverse('api:users:user-logout'))
        assert_view_basic_protected(view, request, self.user_access_token)

        request.session = SessionStore()
        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertTrue(self.user_refresh_token.is_blacklisted)

    def test_logout_all(self) -> None:
        view = UserViewSet.as_view({'post': 'logout_all'})

        if TYPE_CHECKING:
            response: Response

        request: Request = self.factory.post(reverse('api:users:user-logout-all'))
        assert_view_basic_protected(view, request, self.user_access_token)

        request.session = SessionStore()
        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        second_refresh_token: RefreshToken = RefreshToken.for_user(self.user)

        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertTrue(self.user_refresh_token.is_blacklisted)
        self.assertTrue(second_refresh_token.is_blacklisted)

    def test_token_refresh(self) -> None:
        view = UserViewSet.as_view({'post': 'token_refresh'})

        if TYPE_CHECKING:
            request: Request
            response: Response

        second_refresh_token: RefreshToken = RefreshToken.for_user(self.user)
        second_refresh_token.to_blacklist()

        request = self.factory.post(
            reverse('api:users:user-token-refresh'),
            data={'refresh_token': str(second_refresh_token)},
            format='json',
        )
        force_authenticate(request, self.user, None)

        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        request = self.factory.post(
            reverse('api:users:user-token-refresh'),
            data={'refresh_token': str(self.user_refresh_token)},
            format='json',
        )
        force_authenticate(request, self.user, None)

        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_accept_terms(self) -> None:
        view = UserViewSet.as_view({'post': 'accept_terms'})

        if TYPE_CHECKING:
            response: Response

        request: Request = self.factory.post(reverse('api:users:user-accept-terms'))
        assert_view_basic_protected(view, request, self.user_access_token)

        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        self.user.accepted_terms = False
        self.user.terms_accepted_date = None
        self.user.save(update_fields=['accepted_terms', 'terms_accepted_date'])

        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertTrue(self.user.accepted_terms)
        self.assertIsNotNone(self.user.terms_accepted_date)

    def test_destroy(self) -> None:
        view = UserViewSet.as_view({'delete': 'destroy'})

        if TYPE_CHECKING:
            response: Response

        request: Request = self.factory.delete(reverse('api:users:user-detail'))
        assert_view_basic_protected(view, request, self.user_access_token)

        request.session = SessionStore()
        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        second_refresh_token: RefreshToken = RefreshToken.for_user(self.user)

        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        with suppress(User.DoesNotExist):
            self.user.refresh_from_db()
            raise self.failureException('User has not been deleted from database.')

        self.assertTrue(self.user_refresh_token.is_blacklisted)
        self.assertTrue(second_refresh_token.is_blacklisted)
