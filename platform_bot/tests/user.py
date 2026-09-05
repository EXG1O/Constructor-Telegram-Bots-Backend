from django.conf import settings
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory, force_authenticate

from constructor_telegram_bots.utils.tests import assert_view_basic_protected
from users.models import User

from ..models import PlatformBot
from ..views import UserViewSet


class UserViewSetTests(TestCase):
    def setUp(self) -> None:
        self.factory = APIRequestFactory()
        self.list_url: str = reverse('api:platform-bot:user-list')

    def test_create(self) -> None:
        view = UserViewSet.as_view({'post': 'create'})

        telegram_id: int = 1
        first_name: str = 'Test Name'

        request: Request = self.factory.post(
            self.list_url,
            {'telegram_id': telegram_id, 'first_name': first_name},
            format='json',
        )
        assert_view_basic_protected(view, request, settings.PLATFORM_BOT_SERVICE_TOKEN)

        force_authenticate(request, PlatformBot(), settings.PLATFORM_BOT_SERVICE_TOKEN)  # type: ignore [arg-type]

        response: Response = view(request)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        new_user: User = User.objects.get(id=response.data['id'])
        self.assertEqual(new_user.telegram_id, telegram_id)
        self.assertEqual(new_user.first_name, first_name)
