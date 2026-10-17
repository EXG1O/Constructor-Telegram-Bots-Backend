from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient


class StatsAPIViewTestCase(TestCase):
    url: str = reverse('api:telegram-bots:stats')

    def setUp(self) -> None:
        self.client: APIClient = APIClient()

    def test_get_method(self) -> None:
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
