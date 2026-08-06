from django.core.files.storage import default_storage
from django.db.models import QuerySet

from rest_framework.mixins import ListModelMixin, RetrieveModelMixin, UpdateModelMixin
from rest_framework.parsers import JSONParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import GenericViewSet, ModelViewSet

from constructor_telegram_bots.mixins import IDLookupMixin
from constructor_telegram_bots.parsers import MultiPartJSONParser
from constructor_telegram_bots.permissions import ReadOnly
from users.authentication import JWTAuthentication
from users.permissions import IsTermsAccepted

from ..models import Message, MessageDocument, MessageImage
from ..serializers import DiagramMessageSerializer, MessageSerializer
from ..utils.storage import get_media_file_names_queryset
from .mixins import TelegramBotMixin


class MessageViewSet(IDLookupMixin, TelegramBotMixin, ModelViewSet[Message]):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated & (IsTermsAccepted | ReadOnly)]
    parser_classes = [JSONParser, MultiPartJSONParser]
    serializer_class = MessageSerializer

    def get_queryset(self) -> QuerySet[Message]:
        messages: QuerySet[Message] = self.telegram_bot.messages.all()

        if self.action in ['list', 'retrieve']:
            return messages.select_related('settings', 'keyboard').prefetch_related(
                'images', 'documents'
            )

        return messages

    def perform_destroy(self, message: Message) -> None:
        file_names: set[str] = set(
            get_media_file_names_queryset(MessageImage, message=message).union(
                get_media_file_names_queryset(MessageDocument, message=message)
            )
        )

        super().perform_destroy(message)

        for file_name in file_names:
            default_storage.delete(file_name)


class DiagramMessageViewSet(
    IDLookupMixin,
    TelegramBotMixin,
    ListModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
    GenericViewSet[Message],
):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated & (IsTermsAccepted | ReadOnly)]
    serializer_class = DiagramMessageSerializer

    def get_queryset(self) -> QuerySet[Message]:
        messages: QuerySet[Message] = self.telegram_bot.messages.all()

        if self.action in ['list', 'retrieve']:
            return messages.select_related('keyboard').prefetch_related(
                'keyboard__buttons__source_connections__source_object',
                'keyboard__buttons__source_connections__target_object',
                'source_connections__source_object',
                'source_connections__target_object',
            )

        return messages
