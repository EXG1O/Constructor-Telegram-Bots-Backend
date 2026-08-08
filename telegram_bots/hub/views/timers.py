from django.db.models import QuerySet

from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ReadOnlyModelViewSet

from constructor_telegram_bots.mixins import IDLookupMixin

from ...models import Timer
from ..authentication import TokenAuthentication
from ..serializers import TimerSerializer
from .mixins import TelegramBotMixin


class TimerViewSet(IDLookupMixin, TelegramBotMixin, ReadOnlyModelViewSet[Timer]):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = TimerSerializer

    def get_queryset(self) -> QuerySet[Timer]:
        return self.telegram_bot.timers.all()
