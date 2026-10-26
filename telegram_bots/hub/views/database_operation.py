from django.db.models import QuerySet

from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ReadOnlyModelViewSet

from constructor_telegram_bots.mixins import IDLookupMixin

from ...models import DatabaseOperation
from ..authentication import TokenAuthentication
from ..serializers import DatabaseOperationSerializer
from .mixins import TelegramBotMixin


class DatabaseOperationViewSet(
    IDLookupMixin, TelegramBotMixin, ReadOnlyModelViewSet[DatabaseOperation]
):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = DatabaseOperationSerializer

    def get_queryset(self) -> QuerySet[DatabaseOperation]:
        operations: QuerySet[DatabaseOperation] = (
            self.telegram_bot.database_operations.all()
        )

        if self.action in ['list', 'retrieve']:
            return operations.select_related(
                'create_operation', 'update_operation'
            ).prefetch_related('source_connections')

        return operations
