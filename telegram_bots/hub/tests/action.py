from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory, force_authenticate

from constructor_telegram_bots.utils.tests import assert_view_basic_protected
from users.tests.mixins import UserMixin

from ...enums import ActionMessageDeletionTarget
from ...models import ActionMessageDeletion
from ...tests.mixins import ActionMixin, TelegramBotMixin
from ..views import ActionViewSet
from .mixins import HubMixin

from typing import Any


class ActionViewSetTestCase(
    ActionMixin, HubMixin, TelegramBotMixin, UserMixin, TestCase
):
    def setUp(self) -> None:
        super().setUp()

        self.factory = APIRequestFactory()

        ActionMessageDeletion.objects.create(
            action=self.action, target=ActionMessageDeletionTarget.USER_MESSAGE
        )

        self.list_url_kwargs: dict[str, Any] = {'telegram_bot_id': self.telegram_bot.id}
        self.detail_url_kwargs: dict[str, Any] = {
            **self.list_url_kwargs,
            'id': self.action.id,
        }

        self.list_url: str = reverse(
            'api:telegram-bots-hub:telegram-bot-action-list',
            kwargs=self.list_url_kwargs,
        )
        self.detail_url: str = reverse(
            'api:telegram-bots-hub:telegram-bot-action-detail',
            kwargs=self.detail_url_kwargs,
        )

    def test_invalid_telegram_bot_id(self) -> None:
        view = ActionViewSet.as_view({'get': 'list'})

        request: Request = self.factory.get(self.list_url)
        force_authenticate(request, self.hub, self.hub.service_token)  # type: ignore [arg-type]

        view_kwargs: dict[str, Any] = self.list_url_kwargs.copy()
        view_kwargs['telegram_bot_id'] = 0

        response: Response = view(request, **view_kwargs)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_invalid_id(self) -> None:
        view = ActionViewSet.as_view({'get': 'retrieve'})

        request: Request = self.factory.get(self.detail_url)
        force_authenticate(request, self.hub, self.hub.service_token)  # type: ignore [arg-type]

        view_kwargs: dict[str, Any] = self.detail_url_kwargs.copy()
        view_kwargs['id'] = 0

        response: Response = view(request, **view_kwargs)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_list(self) -> None:
        view = ActionViewSet.as_view({'get': 'list'})

        request: Request = self.factory.get(self.list_url)
        assert_view_basic_protected(
            view, request, self.hub.service_token, **self.list_url_kwargs
        )

        force_authenticate(request, self.hub, self.hub.service_token)  # type: ignore [arg-type]

        response: Response = view(request, **self.list_url_kwargs)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve(self) -> None:
        view = ActionViewSet.as_view({'get': 'retrieve'})

        request: Request = self.factory.get(self.detail_url)
        assert_view_basic_protected(
            view, request, self.hub.service_token, **self.detail_url_kwargs
        )

        force_authenticate(request, self.hub, self.hub.service_token)  # type: ignore [arg-type]

        response: Response = view(request, **self.detail_url_kwargs)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
