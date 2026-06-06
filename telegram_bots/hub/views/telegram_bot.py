from django.db.models import QuerySet
from django.utils import timezone

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet

from constructor_telegram_bots.mixins import IDLookupMixin

from ...models import TelegramBot
from ..authentication import TokenAuthentication
from ..models import TelegramBotsHub
from ..serializers import TelegramBotSerializer

from typing import cast


class TelegramBotViewSet(IDLookupMixin, ReadOnlyModelViewSet[TelegramBot]):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = TelegramBotSerializer

    def get_queryset(self) -> QuerySet[TelegramBot]:
        return TelegramBot.objects.all()

    @action(detail=True, methods=['POST'], url_path='hub/assign')
    def assign_hub(self, request: Request, id: int) -> Response:
        hub = cast(TelegramBotsHub, request.user)

        bot: TelegramBot = self.get_object()
        bot.must_be_enabled = True
        bot.is_loading = False
        bot.hub = hub
        bot.save(update_fields=['must_be_enabled', 'is_loading', 'hub'])

        if hub.idle_start_date:
            hub.idle_start_date = None
            hub.save(update_fields=['idle_start_date'])

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['POST'], url_path='hub/unassign')
    def unassign_hub(self, request: Request, id: int) -> Response:
        bot: TelegramBot = self.get_object()
        bot.must_be_enabled = False
        bot.is_loading = False
        bot.hub = None
        bot.save(update_fields=['must_be_enabled', 'is_loading', 'hub'])

        hub = cast(TelegramBotsHub, request.user)

        if hub.bots.count() == 0:
            hub.idle_start_date = timezone.now()
            hub.save(update_fields=['idle_start_date'])

        return Response(status=status.HTTP_204_NO_CONTENT)
