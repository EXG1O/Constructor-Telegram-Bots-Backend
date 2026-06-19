from django.db.models import QuerySet

from rest_framework.mixins import CreateModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ReadOnlyModelViewSet

from django_filters.rest_framework import DjangoFilterBackend, FilterSet

from constructor_telegram_bots.filters import NumberInFilter
from constructor_telegram_bots.mixins import IDLookupMixin
from constructor_telegram_bots.pagination import LimitOffsetPagination

from ...models import Chat
from ..authentication import TokenAuthentication
from ..serializers import ChatSerializer
from .mixins import TelegramBotMixin


class ChatFilter(FilterSet):
    ids = NumberInFilter(field_name='id', lookup_expr='in')
    telegram_ids = NumberInFilter(field_name='telegram_id', lookup_expr='in')

    class Meta:
        model = Chat
        fields = ['ids', 'telegram_ids']


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
    filter_backends = [DjangoFilterBackend]
    filterset_class = ChatFilter

    def get_queryset(self) -> QuerySet[Chat]:
        return self.telegram_bot.chats.all()
