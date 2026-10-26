from django.db.models import QuerySet

from rest_framework.mixins import ListModelMixin, RetrieveModelMixin, UpdateModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import GenericViewSet, ModelViewSet

from constructor_telegram_bots.mixins import IDLookupMixin
from constructor_telegram_bots.permissions import ReadOnly
from users.authentication import JWTAuthentication
from users.permissions import IsTermsAccepted

from ..models import APIRequest
from ..serializers import APIRequestSerializer, DiagramAPIRequestSerializer
from .mixins import TelegramBotMixin


class APIRequestViewSet(IDLookupMixin, TelegramBotMixin, ModelViewSet[APIRequest]):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated & (IsTermsAccepted | ReadOnly)]
    serializer_class = APIRequestSerializer

    def get_queryset(self) -> QuerySet[APIRequest]:
        return self.telegram_bot.api_requests.all()


class DiagramAPIRequestViewSet(
    IDLookupMixin,
    TelegramBotMixin,
    ListModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
    GenericViewSet[APIRequest],
):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated & (IsTermsAccepted | ReadOnly)]
    serializer_class = DiagramAPIRequestSerializer

    def get_queryset(self) -> QuerySet[APIRequest]:
        api_requests: QuerySet[APIRequest] = self.telegram_bot.api_requests.all()

        if self.action in ['list', 'retrieve']:
            return api_requests.prefetch_related('source_connections')

        return api_requests
