from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory

from ..views import StatsAPIView


class StatsAPIViewTests(TestCase):
    url: str = reverse('api:users:stats')

    def setUp(self) -> None:
        self.factory = APIRequestFactory()

    def test_get_method(self) -> None:
        view = StatsAPIView.as_view()
        request: Request = self.factory.get(self.url)
        response: Response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
