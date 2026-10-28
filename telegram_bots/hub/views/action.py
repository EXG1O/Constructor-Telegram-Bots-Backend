from django.db.models import QuerySet

from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ReadOnlyModelViewSet

from constructor_telegram_bots.mixins import IDLookupMixin

from ...models import Action
from ..authentication import TokenAuthentication
from ..serializers import ActionSerializer
from .mixins import TelegramBotMixin


class ActionViewSet(IDLookupMixin, TelegramBotMixin, ReadOnlyModelViewSet[Action]):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = ActionSerializer

    def get_queryset(self) -> QuerySet[Action]:
        actions: QuerySet[Action] = self.telegram_bot.actions.all()

        if self.action in ['list', 'retrieve']:
            return actions.select_related(
                'message_deletion', 'default_keyboard_removal'
            ).prefetch_related('source_connections')

        return actions
