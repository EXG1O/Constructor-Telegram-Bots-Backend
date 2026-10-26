from django.db.models import QuerySet

from rest_framework.mixins import ListModelMixin, RetrieveModelMixin, UpdateModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import GenericViewSet, ModelViewSet

from constructor_telegram_bots.mixins import IDLookupMixin
from constructor_telegram_bots.permissions import ReadOnly
from users.authentication import JWTAuthentication
from users.permissions import IsTermsAccepted

from ..models import DatabaseOperation
from ..serializers import (
    DatabaseOperationSerializer,
    DiagramDatabaseOperationSerializer,
)
from .mixins import TelegramBotMixin


class DatabaseOperationViewSet(
    IDLookupMixin, TelegramBotMixin, ModelViewSet[DatabaseOperation]
):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated & (IsTermsAccepted | ReadOnly)]
    serializer_class = DatabaseOperationSerializer

    def get_queryset(self) -> QuerySet[DatabaseOperation]:
        operations: QuerySet[DatabaseOperation] = (
            self.telegram_bot.database_operations.all()
        )

        if self.action in ['list', 'retrieve']:
            return operations.select_related('create_operation', 'update_operation')

        return operations


class DiagramDatabaseOperationViewSet(
    IDLookupMixin,
    TelegramBotMixin,
    ListModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
    GenericViewSet[DatabaseOperation],
):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated & (IsTermsAccepted | ReadOnly)]
    serializer_class = DiagramDatabaseOperationSerializer

    def get_queryset(self) -> QuerySet[DatabaseOperation]:
        operations: QuerySet[DatabaseOperation] = (
            self.telegram_bot.database_operations.all()
        )

        if self.action in ['list', 'retrieve']:
            return operations.prefetch_related('source_connections')

        return operations
