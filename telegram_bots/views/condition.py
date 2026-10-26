from django.db.models import QuerySet

from rest_framework.mixins import ListModelMixin, RetrieveModelMixin, UpdateModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import GenericViewSet, ModelViewSet

from constructor_telegram_bots.mixins import IDLookupMixin
from constructor_telegram_bots.permissions import ReadOnly
from users.authentication import JWTAuthentication
from users.permissions import IsTermsAccepted

from ..models import Condition
from ..serializers import ConditionSerializer, DiagramConditionSerializer
from .mixins import TelegramBotMixin


class ConditionViewSet(IDLookupMixin, TelegramBotMixin, ModelViewSet[Condition]):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated & (IsTermsAccepted | ReadOnly)]
    serializer_class = ConditionSerializer

    def get_queryset(self) -> QuerySet[Condition]:
        conditions: QuerySet[Condition] = self.telegram_bot.conditions.all()

        if self.action in ['list', 'retrieve']:
            return conditions.prefetch_related('parts')

        return conditions


class DiagramConditionViewSet(
    IDLookupMixin,
    TelegramBotMixin,
    ListModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
    GenericViewSet[Condition],
):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated & (IsTermsAccepted | ReadOnly)]
    serializer_class = DiagramConditionSerializer

    def get_queryset(self) -> QuerySet[Condition]:
        conditions: QuerySet[Condition] = self.telegram_bot.conditions.all()

        if self.action in ['list', 'retrieve']:
            return conditions.prefetch_related('source_connections')

        return conditions
