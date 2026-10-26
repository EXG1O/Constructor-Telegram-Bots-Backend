from django.db.models import QuerySet

from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ReadOnlyModelViewSet

from constructor_telegram_bots.mixins import IDLookupMixin

from ...models import Condition
from ..authentication import TokenAuthentication
from ..serializers import ConditionSerializer
from .mixins import TelegramBotMixin


class ConditionViewSet(
    IDLookupMixin, TelegramBotMixin, ReadOnlyModelViewSet[Condition]
):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = ConditionSerializer

    def get_queryset(self) -> QuerySet[Condition]:
        conditions: QuerySet[Condition] = self.telegram_bot.conditions.all()

        if self.action in ['list', 'retrieve']:
            return conditions.prefetch_related('parts', 'source_connections')

        return conditions
