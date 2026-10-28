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

from ..enums import ActionMessageDeletionTarget
from ..models import Action, ActionMessageDeletion
from ..views import ActionViewSet, DiagramActionViewSet
from .mixins import ActionMixin, TelegramBotMixin

from typing import Any


class ActionViewSetTestCase(ActionMixin, TelegramBotMixin, UserMixin, TestCase):
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
            'api:telegram-bots:telegram-bot-action-list', kwargs=self.list_url_kwargs
        )
        self.detail_url: str = reverse(
            'api:telegram-bots:telegram-bot-action-detail',
            kwargs=self.detail_url_kwargs,
        )

    def test_invalid_telegram_bot_id(self) -> None:
        view = ActionViewSet.as_view({'get': 'list'})

        request: Request = self.factory.get(self.list_url)
        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        view_kwargs: dict[str, Any] = self.list_url_kwargs.copy()
        view_kwargs['telegram_bot_id'] = 0

        response: Response = view(request, **view_kwargs)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_invalid_id(self) -> None:
        view = ActionViewSet.as_view({'get': 'retrieve'})

        request: Request = self.factory.get(self.detail_url)
        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        view_kwargs: dict[str, Any] = self.detail_url_kwargs.copy()
        view_kwargs['id'] = 0

        response: Response = view(request, **view_kwargs)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_list(self) -> None:
        view = ActionViewSet.as_view({'get': 'list'})

        request: Request = self.factory.get(self.list_url)
        assert_view_basic_protected(
            view, request, self.user_access_token, **self.list_url_kwargs
        )

        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        response: Response = view(request, **self.list_url_kwargs)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_with_both_exclusive_fields(self) -> None:
        view = ActionViewSet.as_view({'post': 'create'})

        request: Request = self.factory.post(
            self.list_url,
            {
                'name': 'Test action',
                'message_deletion': {
                    'target': ActionMessageDeletionTarget.USER_MESSAGE
                },
                'default_keyboard_removal': {},
            },
            format='json',
        )
        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        response: Response = view(request, **self.list_url_kwargs)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_without_exclusive_fields(self) -> None:
        view = ActionViewSet.as_view({'post': 'create'})

        request: Request = self.factory.post(
            self.list_url, {'name': 'Test action'}, format='json'
        )
        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        response: Response = view(request, **self.list_url_kwargs)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_over_limit(self) -> None:
        view = ActionViewSet.as_view({'post': 'create'})

        Action.objects.bulk_create(
            Action(telegram_bot=self.telegram_bot, name=f'Test action #{number}')
            for number in range(settings.TELEGRAM_BOT_MAX_ACTIONS)
        )

        request: Request = self.factory.post(
            self.list_url,
            {
                'name': 'Test action',
                'message_deletion': {
                    'target': ActionMessageDeletionTarget.USER_MESSAGE
                },
            },
            format='json',
        )
        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        response: Response = view(request, **self.list_url_kwargs)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create(self) -> None:
        view = ActionViewSet.as_view({'post': 'create'})

        request: Request = self.factory.post(
            self.list_url,
            {
                'name': 'Test action',
                'message_deletion': {
                    'target': ActionMessageDeletionTarget.USER_MESSAGE
                },
            },
            format='json',
        )
        assert_view_basic_protected(
            view, request, self.user_access_token, **self.list_url_kwargs
        )
        assert_view_requires_terms_acceptance(
            view, request, self.user, **self.list_url_kwargs
        )

        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        response: Response = view(request, **self.list_url_kwargs)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_retrieve(self) -> None:
        view = ActionViewSet.as_view({'get': 'retrieve'})

        request: Request = self.factory.get(self.detail_url)
        assert_view_basic_protected(
            view, request, self.user_access_token, **self.detail_url_kwargs
        )

        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        response: Response = view(request, **self.detail_url_kwargs)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update(self) -> None:
        view = ActionViewSet.as_view({'put': 'update'})

        new_name: str = 'New test action'

        request: Request = self.factory.put(
            self.detail_url,
            {
                'name': new_name,
                'message_deletion': {
                    'target': ActionMessageDeletionTarget.LAST_BOT_MESSAGES
                },
            },
            format='json',
        )
        assert_view_basic_protected(
            view, request, self.user_access_token, **self.detail_url_kwargs
        )
        assert_view_requires_terms_acceptance(
            view, request, self.user, **self.detail_url_kwargs
        )

        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        response: Response = view(request, **self.detail_url_kwargs)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.action.refresh_from_db()
        self.assertEqual(self.action.name, new_name)

    def test_partial_update(self) -> None:
        view = ActionViewSet.as_view({'patch': 'partial_update'})

        new_name: str = 'New test action'

        request: Request = self.factory.patch(
            self.detail_url, {'name': new_name}, format='json'
        )
        assert_view_basic_protected(
            view, request, self.user_access_token, **self.detail_url_kwargs
        )
        assert_view_requires_terms_acceptance(
            view, request, self.user, **self.detail_url_kwargs
        )

        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        response: Response = view(request, **self.detail_url_kwargs)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.action.refresh_from_db()
        self.assertEqual(self.action.name, new_name)

    def test_destroy(self) -> None:
        view = ActionViewSet.as_view({'delete': 'destroy'})

        request: Request = self.factory.delete(self.detail_url)
        assert_view_basic_protected(
            view, request, self.user_access_token, **self.detail_url_kwargs
        )
        assert_view_requires_terms_acceptance(
            view, request, self.user, **self.detail_url_kwargs
        )

        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        old_action_count: int = self.telegram_bot.actions.count()
        response: Response = view(request, **self.detail_url_kwargs)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(self.telegram_bot.actions.count(), old_action_count - 1)


class DiagramActionViewSetTestCase(ActionMixin, TelegramBotMixin, UserMixin, TestCase):
    def setUp(self) -> None:
        super().setUp()

        self.factory = APIRequestFactory()

        self.list_url_kwargs: dict[str, Any] = {'telegram_bot_id': self.telegram_bot.id}
        self.detail_url_kwargs: dict[str, Any] = {
            **self.list_url_kwargs,
            'id': self.action.id,
        }

        self.list_url: str = reverse(
            'api:telegram-bots:telegram-bot-diagram-action-list',
            kwargs=self.list_url_kwargs,
        )
        self.detail_url: str = reverse(
            'api:telegram-bots:telegram-bot-diagram-action-detail',
            kwargs=self.detail_url_kwargs,
        )

    def test_invalid_telegram_bot_id(self) -> None:
        view = DiagramActionViewSet.as_view({'get': 'list'})

        request: Request = self.factory.get(self.list_url)
        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        view_kwargs: dict[str, Any] = self.list_url_kwargs.copy()
        view_kwargs['telegram_bot_id'] = 0

        response: Response = view(request, **view_kwargs)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_invalid_id(self) -> None:
        view = DiagramActionViewSet.as_view({'get': 'retrieve'})

        request: Request = self.factory.get(self.detail_url)
        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        view_kwargs: dict[str, Any] = self.detail_url_kwargs.copy()
        view_kwargs['id'] = 0

        response: Response = view(request, **view_kwargs)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_list(self) -> None:
        view = DiagramActionViewSet.as_view({'get': 'list'})

        request: Request = self.factory.get(self.list_url)
        assert_view_basic_protected(
            view, request, self.user_access_token, **self.list_url_kwargs
        )

        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        response: Response = view(request, **self.list_url_kwargs)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve(self) -> None:
        view = DiagramActionViewSet.as_view({'get': 'retrieve'})

        request: Request = self.factory.get(self.detail_url)
        assert_view_basic_protected(
            view, request, self.user_access_token, **self.detail_url_kwargs
        )

        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        response: Response = view(request, **self.detail_url_kwargs)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update(self) -> None:
        view = DiagramActionViewSet.as_view({'put': 'update'})

        new_x: int = 150

        request: Request = self.factory.put(
            self.detail_url, {'x': new_x, 'y': 200}, format='json'
        )
        assert_view_basic_protected(
            view, request, self.user_access_token, **self.detail_url_kwargs
        )
        assert_view_requires_terms_acceptance(
            view, request, self.user, **self.detail_url_kwargs
        )

        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        response: Response = view(request, **self.detail_url_kwargs)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.action.refresh_from_db()
        self.assertEqual(self.action.x, new_x)

    def test_partial_update(self) -> None:
        view = DiagramActionViewSet.as_view({'patch': 'partial_update'})

        new_y: int = 250

        request: Request = self.factory.patch(
            self.detail_url, {'y': new_y}, format='json'
        )
        assert_view_basic_protected(
            view, request, self.user_access_token, **self.detail_url_kwargs
        )
        assert_view_requires_terms_acceptance(
            view, request, self.user, **self.detail_url_kwargs
        )

        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        response: Response = view(request, **self.detail_url_kwargs)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.action.refresh_from_db()
        self.assertEqual(self.action.y, new_y)
