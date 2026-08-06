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

from ..models import Invoice, InvoiceImage
from ..serializers import DiagramInvoiceSerializer, InvoiceSerializer
from ..utils.storage import get_media_file_names_queryset
from .mixins import TelegramBotMixin

from contextlib import suppress


class InvoiceViewSet(IDLookupMixin, TelegramBotMixin, ModelViewSet[Invoice]):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated & (IsTermsAccepted | ReadOnly)]
    parser_classes = [JSONParser, MultiPartJSONParser]
    serializer_class = InvoiceSerializer

    def get_queryset(self) -> QuerySet[Invoice]:
        invoices: QuerySet[Invoice] = self.telegram_bot.invoices.all()

        if self.action in ['list', 'retrieve']:
            return invoices.select_related('image').prefetch_related('prices')

        return invoices

    def perform_destroy(self, invoice: Invoice) -> None:
        file_name: str | None = None

        with suppress(InvoiceImage.DoesNotExist):
            file_name = get_media_file_names_queryset(
                InvoiceImage, invoice=invoice
            ).get()

        super().perform_destroy(invoice)

        if file_name:
            default_storage.delete(file_name)


class DiagramInvoiceViewSet(
    IDLookupMixin,
    TelegramBotMixin,
    ListModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
    GenericViewSet[Invoice],
):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated & (IsTermsAccepted | ReadOnly)]
    serializer_class = DiagramInvoiceSerializer

    def get_queryset(self) -> QuerySet[Invoice]:
        invoices: QuerySet[Invoice] = self.telegram_bot.invoices.all()

        if self.action in ['list', 'retrieve']:
            return invoices.prefetch_related(
                'source_connections__source_object',
                'source_connections__target_object',
            )

        return invoices
