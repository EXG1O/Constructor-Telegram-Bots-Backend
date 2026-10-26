from django.db.models import QuerySet

from rest_framework.mixins import ListModelMixin, RetrieveModelMixin, UpdateModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import GenericViewSet, ModelViewSet

from constructor_telegram_bots.mixins import IDLookupMixin
from constructor_telegram_bots.pagination import LimitOffsetPagination
from constructor_telegram_bots.permissions import ReadOnly
from users.authentication import JWTAuthentication
from users.permissions import IsTermsAccepted

from ..models import TemporaryVariable
from ..serializers import (
    DiagramTemporaryVariableSerializer,
    TemporaryVariableSerializer,
)
from .mixins import TelegramBotMixin


class TemporaryVariableViewSet(
    IDLookupMixin, TelegramBotMixin, ModelViewSet[TemporaryVariable]
):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated & (IsTermsAccepted | ReadOnly)]
    serializer_class = TemporaryVariableSerializer
    pagination_class = LimitOffsetPagination

    def get_queryset(self) -> QuerySet[TemporaryVariable]:
        return self.telegram_bot.temporary_variables.all()


class DiagramTemporaryVariableViewSet(
    IDLookupMixin,
    TelegramBotMixin,
    ListModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
    GenericViewSet[TemporaryVariable],
):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated & (IsTermsAccepted | ReadOnly)]
    serializer_class = DiagramTemporaryVariableSerializer

    def get_queryset(self) -> QuerySet[TemporaryVariable]:
        temporary_variables: QuerySet[TemporaryVariable] = (
            self.telegram_bot.temporary_variables.all()
        )

        if self.action in ['list', 'retrieve']:
            return temporary_variables.prefetch_related('source_connections')

        return temporary_variables
