from django.db.models import QuerySet

from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.mixins import (
    DestroyModelMixin,
    ListModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import GenericViewSet

from django_filters.rest_framework import DjangoFilterBackend

from constructor_telegram_bots.mixins import IDLookupMixin
from constructor_telegram_bots.pagination import LimitOffsetPagination
from constructor_telegram_bots.permissions import ReadOnly
from users.authentication import JWTAuthentication
from users.permissions import IsTermsAccepted

from ..models import Chat
from ..serializers import ChatSerializer
from .mixins import TelegramBotMixin


class ChatViewSet(
    IDLookupMixin,
    TelegramBotMixin,
    ListModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
    DestroyModelMixin,
    GenericViewSet[Chat],
):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated & (IsTermsAccepted | ReadOnly)]
    serializer_class = ChatSerializer
    pagination_class = LimitOffsetPagination
    filter_backends = [SearchFilter, DjangoFilterBackend, OrderingFilter]
    search_fields = ['telegram_id', 'title', 'username', 'first_name', 'last_name']
    filterset_fields = ['type', 'is_allowed', 'is_blocked']
    ordering = ['-id']

    def get_queryset(self) -> QuerySet[Chat]:
        return self.telegram_bot.chats.all()
