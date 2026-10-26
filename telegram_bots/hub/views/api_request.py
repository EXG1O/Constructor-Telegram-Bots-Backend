from django.db.models import QuerySet

from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ReadOnlyModelViewSet

from constructor_telegram_bots.mixins import IDLookupMixin

from ...models import APIRequest
from ..authentication import TokenAuthentication
from ..serializers import APIRequestSerializer
from .mixins import TelegramBotMixin


class APIRequestViewSet(
    IDLookupMixin, TelegramBotMixin, ReadOnlyModelViewSet[APIRequest]
):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = APIRequestSerializer

    def get_queryset(self) -> QuerySet[APIRequest]:
        api_requests: QuerySet[APIRequest] = self.telegram_bot.api_requests.all()

        if self.action in ['list', 'retrieve']:
            return api_requests.prefetch_related('source_connections')

        return api_requests
