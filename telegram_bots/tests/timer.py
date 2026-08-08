from django.conf import settings
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory, force_authenticate

from constructor_telegram_bots.utils.tests import assert_view_basic_protected
from users.tests.mixins import UserMixin
from users.utils.tests import assert_view_requires_terms_acceptance

from ..models import Timer
from ..views import DiagramTimerViewSet, TimerViewSet
from .mixins import TelegramBotMixin, TimerMixin

from typing import TYPE_CHECKING


class TimerViewSetTests(TimerMixin, TelegramBotMixin, UserMixin, TestCase):
    def setUp(self) -> None:
        super().setUp()

        self.factory = APIRequestFactory()

        self.list_true_url: str = reverse(
            'api:telegram-bots:telegram-bot-timer-list',
            kwargs={'telegram_bot_id': self.telegram_bot.id},
        )
        self.list_false_url: str = reverse(
            'api:telegram-bots:telegram-bot-timer-list',
            kwargs={'telegram_bot_id': 0},
        )
        self.detail_true_url: str = reverse(
            'api:telegram-bots:telegram-bot-timer-detail',
            kwargs={'telegram_bot_id': self.telegram_bot.id, 'id': self.timer.id},
        )
        self.detail_false_url_1: str = reverse(
            'api:telegram-bots:telegram-bot-timer-detail',
            kwargs={'telegram_bot_id': 0, 'id': self.timer.id},
        )
        self.detail_false_url_2: str = reverse(
            'api:telegram-bots:telegram-bot-timer-detail',
            kwargs={'telegram_bot_id': self.telegram_bot.id, 'id': 0},
        )

    def test_list(self) -> None:
        view = TimerViewSet.as_view({'get': 'list'})

        if TYPE_CHECKING:
            request: Request
            response: Response

        request = self.factory.get(self.list_true_url)
        assert_view_basic_protected(
            view, request, self.user_access_token, telegram_bot_id=self.telegram_bot.id
        )

        request = self.factory.get(self.list_false_url)
        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        response = view(request, telegram_bot_id=0)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        request = self.factory.get(self.list_true_url)
        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        response = view(request, telegram_bot_id=self.telegram_bot.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create(self) -> None:
        view = TimerViewSet.as_view({'post': 'create'})

        if TYPE_CHECKING:
            request: Request
            response: Response

        request = self.factory.post(self.list_true_url)
        assert_view_basic_protected(
            view, request, self.user_access_token, telegram_bot_id=self.telegram_bot.id
        )
        assert_view_requires_terms_acceptance(
            view, request, self.user, telegram_bot_id=self.telegram_bot.id
        )

        request = self.factory.post(self.list_false_url)
        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        response = view(request, telegram_bot_id=0)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        request = self.factory.post(
            self.list_true_url, {'name': 'Test timer'}, format='json'
        )
        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        response = view(request, telegram_bot_id=self.telegram_bot.id)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        request = self.factory.post(
            self.list_true_url,
            {'name': 'Test timer', 'duration_seconds': 60},
            format='json',
        )
        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        old_timer_count: int = self.telegram_bot.timers.count()

        response = view(request, telegram_bot_id=self.telegram_bot.id)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(self.telegram_bot.timers.count(), old_timer_count + 1)

        Timer.objects.bulk_create(
            Timer(
                telegram_bot=self.telegram_bot,
                name=f'Test timer #{num}',
                duration_seconds=60,
            )
            for num in range(settings.TELEGRAM_BOT_MAX_TIMERS)
        )

        request = self.factory.post(
            self.list_true_url,
            {'name': 'Test timer', 'duration_seconds': 60},
            format='json',
        )
        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        response = view(request, telegram_bot_id=self.telegram_bot.id)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve(self) -> None:
        view = TimerViewSet.as_view({'get': 'retrieve'})

        if TYPE_CHECKING:
            request: Request
            response: Response

        request = self.factory.get(self.detail_true_url)
        assert_view_basic_protected(
            view,
            request,
            self.user_access_token,
            telegram_bot_id=self.telegram_bot.id,
            id=self.timer.id,
        )

        for url in [self.detail_false_url_1, self.detail_false_url_2]:
            request = self.factory.get(url)
            force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

            response = view(request, telegram_bot_id=0, id=self.timer.id)
            self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        request = self.factory.get(self.detail_true_url)
        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        response = view(request, telegram_bot_id=self.telegram_bot.id, id=self.timer.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update(self) -> None:
        view = TimerViewSet.as_view({'put': 'update'})

        if TYPE_CHECKING:
            request: Request
            response: Response

        request = self.factory.put(self.detail_true_url)
        assert_view_basic_protected(
            view,
            request,
            self.user_access_token,
            telegram_bot_id=self.telegram_bot.id,
            id=self.timer.id,
        )
        assert_view_requires_terms_acceptance(
            view,
            request,
            self.user,
            telegram_bot_id=self.telegram_bot.id,
            id=self.timer.id,
        )

        for url in [self.detail_false_url_1, self.detail_false_url_2]:
            request = self.factory.put(url)
            force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

            response = view(request, telegram_bot_id=0, id=self.timer.id)
            self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        new_name: str = 'New test timer'
        new_duration: int = 120

        request = self.factory.put(
            self.detail_true_url,
            {'name': new_name, 'duration_seconds': new_duration},
            format='json',
        )
        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        response = view(request, telegram_bot_id=self.telegram_bot.id, id=self.timer.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.timer.refresh_from_db(fields=['name', 'duration_seconds'])
        self.assertEqual(self.timer.name, new_name)
        self.assertEqual(self.timer.duration_seconds, new_duration)

    def test_partial_update(self) -> None:
        view = TimerViewSet.as_view({'patch': 'partial_update'})

        if TYPE_CHECKING:
            request: Request
            response: Response

        request = self.factory.patch(self.detail_true_url)
        assert_view_basic_protected(
            view,
            request,
            self.user_access_token,
            telegram_bot_id=self.telegram_bot.id,
            id=self.timer.id,
        )
        assert_view_requires_terms_acceptance(
            view,
            request,
            self.user,
            telegram_bot_id=self.telegram_bot.id,
            id=self.timer.id,
        )

        for url in [self.detail_false_url_1, self.detail_false_url_2]:
            request = self.factory.patch(url)
            force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

            response = view(request, telegram_bot_id=0, id=self.timer.id)
            self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        request = self.factory.patch(self.detail_true_url)
        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        response = view(request, telegram_bot_id=self.telegram_bot.id, id=self.timer.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        new_name: str = 'New test timer'

        request = self.factory.patch(
            self.detail_true_url, {'name': new_name}, format='json'
        )
        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        response = view(request, telegram_bot_id=self.telegram_bot.id, id=self.timer.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.timer.refresh_from_db(fields=['name'])
        self.assertEqual(self.timer.name, new_name)

        new_duration: int = 180

        request = self.factory.patch(
            self.detail_true_url, {'duration_seconds': new_duration}, format='json'
        )
        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        response = view(request, telegram_bot_id=self.telegram_bot.id, id=self.timer.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.timer.refresh_from_db(fields=['duration_seconds'])
        self.assertEqual(self.timer.duration_seconds, new_duration)

    def test_destroy(self) -> None:
        view = TimerViewSet.as_view({'delete': 'destroy'})

        if TYPE_CHECKING:
            request: Request
            response: Response

        request = self.factory.delete(self.detail_true_url)
        assert_view_basic_protected(
            view,
            request,
            self.user_access_token,
            telegram_bot_id=self.telegram_bot.id,
            id=self.timer.id,
        )
        assert_view_requires_terms_acceptance(
            view,
            request,
            self.user,
            telegram_bot_id=self.telegram_bot.id,
            id=self.timer.id,
        )

        for url in [self.detail_false_url_1, self.detail_false_url_2]:
            request = self.factory.delete(url)
            force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

            response = view(request, telegram_bot_id=0, id=self.timer.id)
            self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        request = self.factory.delete(self.detail_true_url)
        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        old_timer_count: int = self.telegram_bot.timers.count()

        response = view(request, telegram_bot_id=self.telegram_bot.id, id=self.timer.id)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(self.telegram_bot.timers.count(), old_timer_count - 1)


class DiagramTimerViewSetTests(TimerMixin, TelegramBotMixin, UserMixin, TestCase):
    def setUp(self) -> None:
        super().setUp()

        self.factory = APIRequestFactory()

        self.list_true_url: str = reverse(
            'api:telegram-bots:telegram-bot-diagram-timer-list',
            kwargs={'telegram_bot_id': self.telegram_bot.id},
        )
        self.list_false_url: str = reverse(
            'api:telegram-bots:telegram-bot-diagram-timer-list',
            kwargs={'telegram_bot_id': 0},
        )
        self.detail_true_url: str = reverse(
            'api:telegram-bots:telegram-bot-diagram-timer-detail',
            kwargs={
                'telegram_bot_id': self.telegram_bot.id,
                'id': self.timer.id,
            },
        )
        self.detail_false_url_1: str = reverse(
            'api:telegram-bots:telegram-bot-diagram-timer-detail',
            kwargs={'telegram_bot_id': 0, 'id': self.timer.id},
        )
        self.detail_false_url_2: str = reverse(
            'api:telegram-bots:telegram-bot-diagram-timer-detail',
            kwargs={'telegram_bot_id': self.telegram_bot.id, 'id': 0},
        )

    def test_list(self) -> None:
        view = DiagramTimerViewSet.as_view({'get': 'list'})

        if TYPE_CHECKING:
            request: Request
            response: Response

        request = self.factory.get(self.list_true_url)
        assert_view_basic_protected(
            view, request, self.user_access_token, telegram_bot_id=self.telegram_bot.id
        )

        request = self.factory.get(self.list_false_url)
        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        response = view(request, telegram_bot_id=0)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        request = self.factory.get(self.list_true_url)
        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        response = view(request, telegram_bot_id=self.telegram_bot.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve(self) -> None:
        view = DiagramTimerViewSet.as_view({'get': 'retrieve'})

        if TYPE_CHECKING:
            request: Request
            response: Response

        request = self.factory.get(self.detail_true_url)
        assert_view_basic_protected(
            view,
            request,
            self.user_access_token,
            telegram_bot_id=self.telegram_bot.id,
            id=self.timer.id,
        )

        for url in [self.detail_false_url_1, self.detail_false_url_2]:
            request = self.factory.get(url)
            force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

            response = view(request, telegram_bot_id=0, id=self.timer.id)
            self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        request = self.factory.get(self.detail_true_url)
        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        response = view(request, telegram_bot_id=self.telegram_bot.id, id=self.timer.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
