from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory, force_authenticate

from constructor_telegram_bots.utils.tests import assert_view_basic_protected
from users.tests.mixins import UserMixin
from users.utils.tests import assert_view_requires_terms_acceptance

from ..models import TelegramBot
from ..views import TelegramBotViewSet
from .mixins import TelegramBotMixin

from contextlib import suppress
from typing import TYPE_CHECKING, Any


class TelegramBotViewSetTests(TelegramBotMixin, UserMixin, TestCase):
    list_url: str = reverse('api:telegram-bots:telegram-bot-list')

    def setUp(self) -> None:
        super().setUp()

        self.factory = APIRequestFactory()

        true_kwargs: dict[str, Any] = {'id': self.telegram_bot.id}
        false_kwargs: dict[str, Any] = {'id': 0}

        self.detail_true_url: str = reverse(
            'api:telegram-bots:telegram-bot-detail', kwargs=true_kwargs
        )
        self.detail_false_url: str = reverse(
            'api:telegram-bots:telegram-bot-detail', kwargs=false_kwargs
        )
        self.start_true_url: str = reverse(
            'api:telegram-bots:telegram-bot-start', kwargs=true_kwargs
        )
        self.start_false_url: str = reverse(
            'api:telegram-bots:telegram-bot-start', kwargs=false_kwargs
        )
        self.restart_true_url: str = reverse(
            'api:telegram-bots:telegram-bot-restart', kwargs=true_kwargs
        )
        self.restart_false_url: str = reverse(
            'api:telegram-bots:telegram-bot-restart', kwargs=false_kwargs
        )
        self.stop_true_url: str = reverse(
            'api:telegram-bots:telegram-bot-stop', kwargs=true_kwargs
        )
        self.stop_false_url: str = reverse(
            'api:telegram-bots:telegram-bot-stop', kwargs=false_kwargs
        )

    def test_list(self) -> None:
        view = TelegramBotViewSet.as_view({'get': 'list'})

        if TYPE_CHECKING:
            response: Response

        request: Request = self.factory.get(self.list_url)
        assert_view_basic_protected(view, request, self.user_access_token)

        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create(self) -> None:
        view = TelegramBotViewSet.as_view({'post': 'create'})

        if TYPE_CHECKING:
            request: Request
            response: Response

        request = self.factory.post(self.list_url)
        assert_view_basic_protected(view, request, self.user_access_token)

        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        assert_view_requires_terms_acceptance(view, request, self.user)

        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        request = self.factory.post(
            self.list_url, {'api_token': 'Bye!', 'is_private': False}, format='json'
        )
        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        old_telegram_bot_count: int = self.user.telegram_bots.count()

        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(self.user.telegram_bots.count(), old_telegram_bot_count + 1)

    def test_retrieve(self) -> None:
        view = TelegramBotViewSet.as_view({'get': 'retrieve'})

        if TYPE_CHECKING:
            request: Request
            response: Response

        request = self.factory.get(self.detail_true_url)
        assert_view_basic_protected(
            view, request, self.user_access_token, id=self.telegram_bot.id
        )

        request = self.factory.get(self.detail_false_url)
        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        response = view(request, id=0)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        request = self.factory.get(self.detail_true_url)
        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        response = view(request, id=self.telegram_bot.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_start(self) -> None:
        view = TelegramBotViewSet.as_view({'post': 'start'})

        if TYPE_CHECKING:
            request: Request
            response: Response

        request = self.factory.post(self.start_true_url)
        assert_view_basic_protected(
            view, request, self.user_access_token, id=self.telegram_bot.id
        )
        assert_view_requires_terms_acceptance(
            view, request, self.user, id=self.telegram_bot.id
        )

        request = self.factory.post(self.start_false_url)
        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        response = view(request, id=0)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        request = self.factory.post(self.start_true_url)
        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        response = view(request, id=self.telegram_bot.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_restart(self) -> None:
        view = TelegramBotViewSet.as_view({'post': 'restart'})

        if TYPE_CHECKING:
            request: Request
            response: Response

        request = self.factory.post(self.restart_true_url)
        assert_view_basic_protected(
            view, request, self.user_access_token, id=self.telegram_bot.id
        )
        assert_view_requires_terms_acceptance(
            view, request, self.user, id=self.telegram_bot.id
        )

        request = self.factory.post(self.restart_false_url)
        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        response = view(request, id=0)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        request = self.factory.post(self.restart_true_url)
        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        response = view(request, id=self.telegram_bot.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_stop(self) -> None:
        view = TelegramBotViewSet.as_view({'post': 'stop'})

        if TYPE_CHECKING:
            request: Request
            response: Response

        request = self.factory.post(self.stop_true_url)
        assert_view_basic_protected(
            view, request, self.user_access_token, id=self.telegram_bot.id
        )
        assert_view_requires_terms_acceptance(
            view, request, self.user, id=self.telegram_bot.id
        )

        request = self.factory.post(self.stop_false_url)
        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        response = view(request, id=0)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        request = self.factory.post(self.stop_true_url)
        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        response = view(request, id=self.telegram_bot.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update(self) -> None:
        view = TelegramBotViewSet.as_view({'put': 'update'})

        if TYPE_CHECKING:
            request: Request
            response: Response

        request = self.factory.put(self.detail_true_url)
        assert_view_basic_protected(
            view, request, self.user_access_token, id=self.telegram_bot.id
        )
        assert_view_requires_terms_acceptance(
            view, request, self.user, id=self.telegram_bot.id
        )

        request = self.factory.put(self.detail_false_url)
        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        response = view(request, id=0)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        request = self.factory.put(self.detail_true_url, format='json')
        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        response = view(request, id=self.telegram_bot.id)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        new_api_token: str = '123456789:exg1o'

        request = self.factory.put(
            self.detail_true_url, {'api_token': new_api_token}, format='json'
        )
        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        response = view(request, id=self.telegram_bot.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.telegram_bot.refresh_from_db()
        self.assertEqual(self.telegram_bot.api_token, new_api_token)

    def test_partial_update(self) -> None:
        view = TelegramBotViewSet.as_view({'patch': 'partial_update'})

        if TYPE_CHECKING:
            request: Request
            response: Response

        request = self.factory.patch(self.detail_true_url)
        assert_view_basic_protected(
            view, request, self.user_access_token, id=self.telegram_bot.id
        )
        assert_view_requires_terms_acceptance(
            view, request, self.user, id=self.telegram_bot.id
        )

        request = self.factory.patch(self.detail_false_url)
        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        response = view(request, id=0)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        request = self.factory.patch(self.detail_true_url)
        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        response = view(request, id=self.telegram_bot.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        new_api_token: str = '123456789:exg1o'

        request = self.factory.patch(
            self.detail_true_url, {'api_token': new_api_token}, format='json'
        )
        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        response = view(request, id=self.telegram_bot.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.telegram_bot.refresh_from_db()
        self.assertEqual(self.telegram_bot.api_token, new_api_token)

    def test_destroy(self) -> None:
        view = TelegramBotViewSet.as_view({'delete': 'destroy'})

        if TYPE_CHECKING:
            request: Request
            response: Response

        request = self.factory.delete(self.detail_true_url)
        assert_view_basic_protected(
            view, request, self.user_access_token, id=self.telegram_bot.id
        )
        assert_view_requires_terms_acceptance(
            view, request, self.user, id=self.telegram_bot.id
        )

        request = self.factory.delete(self.detail_false_url)
        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        response = view(request, id=0)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        request = self.factory.delete(self.detail_true_url)
        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        response = view(request, id=self.telegram_bot.id)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        with suppress(TelegramBot.DoesNotExist):
            self.telegram_bot.refresh_from_db()
            raise self.failureException(
                'Telegram bot has not been deleted from database!'
            )
