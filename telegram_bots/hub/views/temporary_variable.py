from django.db.models import QuerySet

from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ReadOnlyModelViewSet

from constructor_telegram_bots.mixins import IDLookupMixin

from ...models import TemporaryVariable
from ..authentication import TokenAuthentication
from ..serializers import TemporaryVariableSerializer
from .mixins import TelegramBotMixin


class TemporaryVariableViewSet(
    IDLookupMixin, TelegramBotMixin, ReadOnlyModelViewSet[TemporaryVariable]
):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = TemporaryVariableSerializer

    def get_queryset(self) -> QuerySet[TemporaryVariable]:
        temporary_variables: QuerySet[TemporaryVariable] = (
            self.telegram_bot.temporary_variables.all()
        )

        if self.action in ['list', 'retrieve']:
            return temporary_variables.prefetch_related('source_connections')

        return temporary_variables
