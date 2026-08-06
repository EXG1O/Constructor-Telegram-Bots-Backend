from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory

from .views import SectionViewSet


class SectionViewSetTests(TestCase):
    url: str = reverse('api:instruction:section-list')

    def setUp(self) -> None:
        self.factory = APIRequestFactory()

    def test_list(self) -> None:
        view = SectionViewSet.as_view({'get': 'list'})
        request: Request = self.factory.get(self.url)
        response: Response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
