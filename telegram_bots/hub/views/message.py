from django.db.models import QuerySet

from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ReadOnlyModelViewSet

from django_filters.rest_framework import ChoiceFilter, DjangoFilterBackend, FilterSet

from constructor_telegram_bots.filters import NumberInFilter
from constructor_telegram_bots.mixins import IDLookupMixin

from ...enums import KeyboardType
from ...models import Message, MessageKeyboardButton
from ..authentication import TokenAuthentication
from ..serializers import MessageKeyboardButtonSerializer, MessageSerializer
from .mixins import TelegramBotMixin


class MessageViewSet(IDLookupMixin, TelegramBotMixin, ReadOnlyModelViewSet[Message]):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = MessageSerializer

    def get_queryset(self) -> QuerySet[Message]:
        messages: QuerySet[Message] = self.telegram_bot.messages.all()

        if self.action in ['list', 'retrieve']:
            return messages.select_related('settings', 'keyboard').prefetch_related(
                'images',
                'documents',
                'keyboard__buttons__source_connections__source_object',
                'keyboard__buttons__source_connections__target_object',
                'source_connections__source_object',
                'source_connections__target_object',
            )

        return messages


class MessageKeyboardButtonFilter(FilterSet):
    ids = NumberInFilter(field_name='id', lookup_expr='in')
    type = ChoiceFilter(field_name='keyboard__type', choices=KeyboardType.choices)

    class Meta:
        model = MessageKeyboardButton
        fields = ['ids', 'type', 'text']


class MessageKeyboardButtonViewSet(
    IDLookupMixin, TelegramBotMixin, ReadOnlyModelViewSet[MessageKeyboardButton]
):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = MessageKeyboardButtonSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = MessageKeyboardButtonFilter

    def get_queryset(self) -> QuerySet[MessageKeyboardButton]:
        return MessageKeyboardButton.objects.filter(
            keyboard__message__telegram_bot=self.telegram_bot
        ).prefetch_related(
            'source_connections__source_object',
            'source_connections__target_object',
        )
