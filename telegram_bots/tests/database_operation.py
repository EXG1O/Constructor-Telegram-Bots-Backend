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

from ..models import DatabaseOperation
from ..views import DatabaseOperationViewSet, DiagramDatabaseOperationViewSet
from .mixins import DatabaseOperationMixin, TelegramBotMixin

from contextlib import suppress
from typing import TYPE_CHECKING


class DatabaseOperationViewSetTests(
    DatabaseOperationMixin, TelegramBotMixin, UserMixin, TestCase
):
    def setUp(self) -> None:
        super().setUp()

        self.factory = APIRequestFactory()

        self.list_true_url: str = reverse(
            'api:telegram-bots:telegram-bot-database-operation-list',
            kwargs={'telegram_bot_id': self.telegram_bot.id},
        )
        self.list_false_url: str = reverse(
            'api:telegram-bots:telegram-bot-database-operation-list',
            kwargs={'telegram_bot_id': 0},
        )
        self.detail_true_url: str = reverse(
            'api:telegram-bots:telegram-bot-database-operation-detail',
            kwargs={
                'telegram_bot_id': self.telegram_bot.id,
                'id': self.database_operation.id,
            },
        )
        self.detail_false_url_1: str = reverse(
            'api:telegram-bots:telegram-bot-database-operation-detail',
            kwargs={'telegram_bot_id': 0, 'id': self.database_operation.id},
        )
        self.detail_false_url_2: str = reverse(
            'api:telegram-bots:telegram-bot-database-operation-detail',
            kwargs={'telegram_bot_id': self.telegram_bot.id, 'id': 0},
        )

    def test_list(self) -> None:
        view = DatabaseOperationViewSet.as_view({'get': 'list'})

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
        view = DatabaseOperationViewSet.as_view({'post': 'create'})

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

        request = self.factory.post(self.list_true_url)
        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        response = view(request, telegram_bot_id=self.telegram_bot.id)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        request = self.factory.post(
            self.list_true_url,
            {'name': 'Test name'},
            format='json',
        )
        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        response = view(request, telegram_bot_id=self.telegram_bot.id)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        request = self.factory.post(
            self.list_true_url,
            {'name': 'Test name', 'create_operation': {'data': {'key': 'value'}}},
            format='json',
        )
        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        old_database_operation_count: int = (
            self.telegram_bot.database_operations.count()
        )

        response = view(request, telegram_bot_id=self.telegram_bot.id)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            self.telegram_bot.database_operations.count(),
            old_database_operation_count + 1,
        )

        DatabaseOperation.objects.bulk_create(
            DatabaseOperation(
                telegram_bot=self.telegram_bot, name=f'Test database operation #{num}'
            )
            for num in range(settings.TELEGRAM_BOT_MAX_DATABASE_OPERATIONS)
        )

        request = self.factory.post(
            self.list_true_url,
            {'name': 'Test name', 'create_operation': {'data': {'key': 'value'}}},
            format='json',
        )
        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        response = view(request, telegram_bot_id=self.telegram_bot.id)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve(self) -> None:
        view = DatabaseOperationViewSet.as_view({'get': 'retrieve'})

        if TYPE_CHECKING:
            request: Request
            response: Response

        request = self.factory.get(self.detail_true_url)
        assert_view_basic_protected(
            view,
            request,
            self.user_access_token,
            telegram_bot_id=self.telegram_bot.id,
            id=self.database_operation.id,
        )

        for url in [self.detail_false_url_1, self.detail_false_url_2]:
            request = self.factory.get(url)
            force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

            response = view(request, telegram_bot_id=0, id=self.database_operation.id)
            self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        request = self.factory.get(self.detail_true_url)
        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        response = view(
            request, telegram_bot_id=self.telegram_bot.id, id=self.database_operation.id
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update(self) -> None:
        view = DatabaseOperationViewSet.as_view({'put': 'update'})

        if TYPE_CHECKING:
            request: Request
            response: Response

        request = self.factory.put(self.detail_true_url)
        assert_view_basic_protected(
            view,
            request,
            self.user_access_token,
            telegram_bot_id=self.telegram_bot.id,
            id=self.database_operation.id,
        )
        assert_view_requires_terms_acceptance(
            view,
            request,
            self.user,
            telegram_bot_id=self.telegram_bot.id,
            id=self.database_operation.id,
        )

        for url in [self.detail_false_url_1, self.detail_false_url_2]:
            request = self.factory.put(url)
            force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

            response = view(request, telegram_bot_id=0, id=self.database_operation.id)
            self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        new_name: str = 'New test name'

        request = self.factory.put(
            self.detail_true_url, {'name': new_name}, format='json'
        )
        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        response = view(
            request, telegram_bot_id=self.telegram_bot.id, id=self.database_operation.id
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        request = self.factory.put(
            self.detail_true_url,
            {
                'name': new_name,
                'update_operation': {
                    'overwrite': True,
                    'lookup_field_name': 'user_id',
                    'lookup_field_value': '123456789',
                    'create_if_not_found': False,
                    'new_data': {'key': 'New value'},
                },
            },
            format='json',
        )
        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        response = view(
            request, telegram_bot_id=self.telegram_bot.id, id=self.database_operation.id
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.database_operation.refresh_from_db(fields=['name'])
        self.assertEqual(self.database_operation.name, new_name)

    def test_partial_update(self) -> None:
        view = DatabaseOperationViewSet.as_view({'patch': 'partial_update'})

        if TYPE_CHECKING:
            request: Request
            response: Response

        request = self.factory.patch(self.detail_true_url)
        assert_view_basic_protected(
            view,
            request,
            self.user_access_token,
            telegram_bot_id=self.telegram_bot.id,
            id=self.database_operation.id,
        )
        assert_view_requires_terms_acceptance(
            view,
            request,
            self.user,
            telegram_bot_id=self.telegram_bot.id,
            id=self.database_operation.id,
        )

        for url in [self.detail_false_url_1, self.detail_false_url_2]:
            request = self.factory.patch(url)
            force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

            response = view(request, telegram_bot_id=0, id=self.database_operation.id)
            self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        request = self.factory.patch(self.detail_true_url)
        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        response = view(
            request, telegram_bot_id=self.telegram_bot.id, id=self.database_operation.id
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        new_name: str = 'New test name'

        request = self.factory.patch(
            self.detail_true_url,
            {
                'name': new_name,
                'update_operation': {
                    'overwrite': True,
                    'lookup_field_name': 'user_id',
                    'lookup_field_value': '123456789',
                    'create_if_not_found': False,
                    'new_data': {'key': 'New value'},
                },
            },
            format='json',
        )
        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        response = view(
            request, telegram_bot_id=self.telegram_bot.id, id=self.database_operation.id
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        request = self.factory.patch(
            self.detail_true_url, {'name': new_name}, format='json'
        )
        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        response = view(
            request, telegram_bot_id=self.telegram_bot.id, id=self.database_operation.id
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.database_operation.refresh_from_db(fields=['name'])
        self.assertEqual(self.database_operation.name, new_name)

    def test_destroy(self) -> None:
        view = DatabaseOperationViewSet.as_view({'delete': 'destroy'})

        if TYPE_CHECKING:
            request: Request
            response: Response

        request = self.factory.delete(self.detail_true_url)
        assert_view_basic_protected(
            view,
            request,
            self.user_access_token,
            telegram_bot_id=self.telegram_bot.id,
            id=self.database_operation.id,
        )
        assert_view_requires_terms_acceptance(
            view,
            request,
            self.user,
            telegram_bot_id=self.telegram_bot.id,
            id=self.database_operation.id,
        )

        for url in [self.detail_false_url_1, self.detail_false_url_2]:
            request = self.factory.delete(url)
            force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

            response = view(request, telegram_bot_id=0, id=self.database_operation.id)
            self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        request = self.factory.delete(self.detail_true_url)
        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        response = view(
            request, telegram_bot_id=self.telegram_bot.id, id=self.database_operation.id
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        with suppress(DatabaseOperation.DoesNotExist):
            self.database_operation.refresh_from_db()
            raise self.failureException(
                'Database operation has not been deleted from database.'
            )


class DiagramDatabaseOperationViewSetTests(
    DatabaseOperationMixin, TelegramBotMixin, UserMixin, TestCase
):
    def setUp(self) -> None:
        super().setUp()

        self.factory = APIRequestFactory()

        self.list_true_url: str = reverse(
            'api:telegram-bots:telegram-bot-diagram-database-operation-list',
            kwargs={'telegram_bot_id': self.telegram_bot.id},
        )
        self.list_false_url: str = reverse(
            'api:telegram-bots:telegram-bot-diagram-database-operation-list',
            kwargs={'telegram_bot_id': 0},
        )
        self.detail_true_url: str = reverse(
            'api:telegram-bots:telegram-bot-diagram-database-operation-detail',
            kwargs={
                'telegram_bot_id': self.telegram_bot.id,
                'id': self.database_operation.id,
            },
        )
        self.detail_false_url_1: str = reverse(
            'api:telegram-bots:telegram-bot-diagram-database-operation-detail',
            kwargs={'telegram_bot_id': 0, 'id': self.database_operation.id},
        )
        self.detail_false_url_2: str = reverse(
            'api:telegram-bots:telegram-bot-diagram-database-operation-detail',
            kwargs={'telegram_bot_id': self.telegram_bot.id, 'id': 0},
        )

    def test_list(self) -> None:
        view = DiagramDatabaseOperationViewSet.as_view({'get': 'list'})

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
        view = DiagramDatabaseOperationViewSet.as_view({'get': 'retrieve'})

        if TYPE_CHECKING:
            request: Request
            response: Response

        request = self.factory.get(self.detail_true_url)
        assert_view_basic_protected(
            view,
            request,
            self.user_access_token,
            telegram_bot_id=self.telegram_bot.id,
            id=self.database_operation.id,
        )

        for url in [self.detail_false_url_1, self.detail_false_url_2]:
            request = self.factory.get(url)
            force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

            response = view(request, telegram_bot_id=0, id=self.database_operation.id)
            self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        request = self.factory.get(self.detail_true_url)
        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        response = view(
            request, telegram_bot_id=self.telegram_bot.id, id=self.database_operation.id
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update(self) -> None:
        view = DiagramDatabaseOperationViewSet.as_view({'put': 'update'})

        if TYPE_CHECKING:
            request: Request
            response: Response

        request = self.factory.put(self.detail_true_url)
        assert_view_basic_protected(
            view,
            request,
            self.user_access_token,
            telegram_bot_id=self.telegram_bot.id,
            id=self.database_operation.id,
        )
        assert_view_requires_terms_acceptance(
            view,
            request,
            self.user,
            telegram_bot_id=self.telegram_bot.id,
            id=self.database_operation.id,
        )

        for url in [self.detail_false_url_1, self.detail_false_url_2]:
            request = self.factory.put(url)
            force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

            response = view(request, telegram_bot_id=0, id=self.database_operation.id)
            self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        request = self.factory.put(self.detail_true_url)
        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        response = view(
            request, telegram_bot_id=self.telegram_bot.id, id=self.database_operation.id
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        new_x: int = 150

        request = self.factory.put(
            self.detail_true_url, {'x': new_x, 'y': 200}, format='json'
        )
        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        response = view(
            request, telegram_bot_id=self.telegram_bot.id, id=self.database_operation.id
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.database_operation.refresh_from_db(fields=['x'])
        self.assertEqual(self.database_operation.x, new_x)

    def test_partial_update(self) -> None:
        view = DiagramDatabaseOperationViewSet.as_view({'patch': 'partial_update'})

        if TYPE_CHECKING:
            request: Request
            response: Response

        request = self.factory.patch(self.detail_true_url)
        assert_view_basic_protected(
            view,
            request,
            self.user_access_token,
            telegram_bot_id=self.telegram_bot.id,
            id=self.database_operation.id,
        )
        assert_view_requires_terms_acceptance(
            view,
            request,
            self.user,
            telegram_bot_id=self.telegram_bot.id,
            id=self.database_operation.id,
        )

        for url in [self.detail_false_url_1, self.detail_false_url_2]:
            request = self.factory.patch(url)
            force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

            response = view(request, telegram_bot_id=0, id=self.database_operation.id)
            self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        request = self.factory.patch(self.detail_true_url)
        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        response = view(
            request, telegram_bot_id=self.telegram_bot.id, id=self.database_operation.id
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        new_x: int = 150

        request = self.factory.patch(self.detail_true_url, {'x': new_x}, format='json')
        force_authenticate(request, self.user, self.user_access_token)  # type: ignore [arg-type]

        response = view(
            request, telegram_bot_id=self.telegram_bot.id, id=self.database_operation.id
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.database_operation.refresh_from_db(fields=['x'])
        self.assertEqual(self.database_operation.x, new_x)
