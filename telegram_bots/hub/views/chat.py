from django.db.models import QuerySet

from rest_framework.mixins import CreateModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ReadOnlyModelViewSet

from constructor_telegram_bots.mixins import IDLookupMixin
from constructor_telegram_bots.pagination import LimitOffsetPagination

from ...models import Chat
from ..authentication import TokenAuthentication
from ..serializers import ChatSerializer
from .mixins import TelegramBotMixin


class ChatViewSet(
    IDLookupMixin,
    TelegramBotMixin,
    CreateModelMixin,
    ReadOnlyModelViewSet[Chat],
):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = ChatSerializer
    pagination_class = LimitOffsetPagination

    def get_queryset(self) -> QuerySet[Chat]:
        return self.telegram_bot.chats.all()
