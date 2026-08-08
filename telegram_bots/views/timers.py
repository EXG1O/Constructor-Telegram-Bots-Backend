from django.db.models import QuerySet

from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from constructor_telegram_bots.mixins import IDLookupMixin
from constructor_telegram_bots.permissions import ReadOnly
from users.authentication import JWTAuthentication
from users.permissions import IsTermsAccepted

from ..models import Timer
from ..serializers import DiagramTimerSerializer, TimerSerializer
from .mixins import TelegramBotMixin


class TimerViewSet(IDLookupMixin, TelegramBotMixin, ModelViewSet[Timer]):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated & (IsTermsAccepted | ReadOnly)]
    serializer_class = TimerSerializer

    def get_queryset(self) -> QuerySet[Timer]:
        return self.telegram_bot.timers.all()


class DiagramTimerViewSet(IDLookupMixin, TelegramBotMixin, ModelViewSet[Timer]):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated & (IsTermsAccepted | ReadOnly)]
    serializer_class = DiagramTimerSerializer

    def get_queryset(self) -> QuerySet[Timer]:
        timers: QuerySet[Timer] = self.telegram_bot.timers.all()

        if self.action in ['list', 'retrieve']:
            return timers.prefetch_related(
                'source_connections__source_object',
                'source_connections__target_object',
            )

        return timers
