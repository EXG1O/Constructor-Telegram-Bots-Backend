from django.db.models import QuerySet

from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ReadOnlyModelViewSet

from constructor_telegram_bots.mixins import IDLookupMixin

from ...models import Randomizer
from ..authentication import TokenAuthentication
from ..serializers import RandomizerSerializer
from .mixins import TelegramBotMixin


class RandomizerViewSet(
    IDLookupMixin, TelegramBotMixin, ReadOnlyModelViewSet[Randomizer]
):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = RandomizerSerializer

    def get_queryset(self) -> QuerySet[Randomizer]:
        randomizers: QuerySet[Randomizer] = self.telegram_bot.randomizers.all()

        if self.action in ['list', 'retrieve']:
            return randomizers.prefetch_related(
                'source_connections__source_object', 'source_connections__target_object'
            )

        return randomizers
