from django.core.files.storage import default_storage
from django.db.models import QuerySet

from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from constructor_telegram_bots.mixins import IDLookupMixin
from constructor_telegram_bots.permissions import ReadOnly
from users.authentication import JWTAuthentication
from users.permissions import IsTermsAccepted

from ..models import TelegramBot
from ..serializers import TelegramBotSerializer
from ..utils.storage import get_telegram_bot_file_names


class TelegramBotViewSet(IDLookupMixin, ModelViewSet[TelegramBot]):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated & (IsTermsAccepted | ReadOnly)]
    serializer_class = TelegramBotSerializer

    def get_queryset(self) -> QuerySet[TelegramBot]:
        return self.request.user.telegram_bots.all()  # type: ignore [union-attr]

    @action(detail=True, methods=['POST'])
    def start(self, request: Request, id: int) -> Response:
        telegram_bot: TelegramBot = self.get_object()
        telegram_bot.start()

        return Response(self.get_serializer(telegram_bot).data)

    @action(detail=True, methods=['POST'])
    def restart(self, request: Request, id: int) -> Response:
        telegram_bot: TelegramBot = self.get_object()
        telegram_bot.restart()

        return Response(self.get_serializer(telegram_bot).data)

    @action(detail=True, methods=['POST'])
    def stop(self, request: Request, id: int) -> Response:
        telegram_bot: TelegramBot = self.get_object()
        telegram_bot.stop()

        return Response(self.get_serializer(telegram_bot).data)

    def perform_destroy(self, telegram_bot: TelegramBot) -> None:
        file_names: set[str] = get_telegram_bot_file_names(telegram_bot=telegram_bot)

        if telegram_bot.is_enabled:
            telegram_bot.stop(save=False)

        super().perform_destroy(telegram_bot)

        for file_name in file_names:
            default_storage.delete(file_name)
