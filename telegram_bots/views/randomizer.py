from django.db.models import QuerySet

from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from constructor_telegram_bots.mixins import IDLookupMixin
from constructor_telegram_bots.permissions import ReadOnly
from users.authentication import JWTAuthentication
from users.permissions import IsTermsAccepted

from ..models import Randomizer
from ..serializers import DiagramRandomizerSerializer, RandomizerSerializer
from .mixins import TelegramBotMixin


class RandomizerViewSet(IDLookupMixin, TelegramBotMixin, ModelViewSet[Randomizer]):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated & (IsTermsAccepted | ReadOnly)]
    serializer_class = RandomizerSerializer

    def get_queryset(self) -> QuerySet[Randomizer]:
        return self.telegram_bot.randomizers.all()


class DiagramRandomizerViewSet(
    IDLookupMixin, TelegramBotMixin, ModelViewSet[Randomizer]
):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated & (IsTermsAccepted | ReadOnly)]
    serializer_class = DiagramRandomizerSerializer

    def get_queryset(self) -> QuerySet[Randomizer]:
        randomizers: QuerySet[Randomizer] = self.telegram_bot.randomizers.all()

        if self.action in ['list', 'retrieve']:
            return randomizers.prefetch_related(
                'source_connections__source_object',
                'source_connections__target_object',
            )

        return randomizers
