from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory

from users.tests.mixins import UserMixin

from .enums import DocumentType
from .models import Document
from .views import DocumentViewSet


class SubscriptionInvoiceViewSetTests(UserMixin, TestCase):
    url: str = reverse(
        'api:legal:document-detail', kwargs={'type': DocumentType.TERMS_OF_SERVICE}
    )

    def setUp(self) -> None:
        super().setUp()
        self.factory = APIRequestFactory()
        self.document: Document = Document.objects.create(
            type=DocumentType.TERMS_OF_SERVICE, content=''
        )

    def test_retrieve(self) -> None:
        view = DocumentViewSet.as_view({'get': 'retrieve'})
        request: Request = self.factory.get(self.url)
        response: Response = view(request, type=DocumentType.TERMS_OF_SERVICE)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
