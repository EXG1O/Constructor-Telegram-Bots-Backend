from django.db.models import QuerySet

from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ReadOnlyModelViewSet

from constructor_telegram_bots.mixins import IDLookupMixin

from ...models import Invoice
from ..authentication import TokenAuthentication
from ..serializers import InvoiceSerializer
from .mixins import TelegramBotMixin


class InvoiceViewSet(IDLookupMixin, TelegramBotMixin, ReadOnlyModelViewSet[Invoice]):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = InvoiceSerializer

    def get_queryset(self) -> QuerySet[Invoice]:
        invoices: QuerySet[Invoice] = self.telegram_bot.invoices.all()

        if self.action in ['list', 'retrieve']:
            return invoices.select_related('image').prefetch_related(
                'prices', 'source_connections'
            )

        return invoices
