from django.db.models import QuerySet

from rest_framework.mixins import ListModelMixin, RetrieveModelMixin, UpdateModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import GenericViewSet, ModelViewSet

from constructor_telegram_bots.mixins import IDLookupMixin
from constructor_telegram_bots.permissions import ReadOnly
from users.authentication import JWTAuthentication
from users.permissions import IsTermsAccepted

from ..models import Action
from ..serializers import ActionSerializer, DiagramActionSerializer
from .mixins import TelegramBotMixin


class ActionViewSet(IDLookupMixin, TelegramBotMixin, ModelViewSet[Action]):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated & (IsTermsAccepted | ReadOnly)]
    serializer_class = ActionSerializer

    def get_queryset(self) -> QuerySet[Action]:
        actions: QuerySet[Action] = self.telegram_bot.actions.all()

        if self.action in ['list', 'retrieve']:
            return actions.select_related(
                'message_deletion', 'default_keyboard_removal'
            )

        return actions


class DiagramActionViewSet(
    IDLookupMixin,
    TelegramBotMixin,
    ListModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
    GenericViewSet[Action],
):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated & (IsTermsAccepted | ReadOnly)]
    serializer_class = DiagramActionSerializer

    def get_queryset(self) -> QuerySet[Action]:
        actions: QuerySet[Action] = self.telegram_bot.actions.all()

        if self.action in ['list', 'retrieve']:
            return actions.prefetch_related('source_connections')

        return actions
