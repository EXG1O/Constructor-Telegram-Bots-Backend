from django.db.models import QuerySet
from django.shortcuts import get_object_or_404
from django.utils.functional import cached_property

from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from constructor_telegram_bots.mixins import IDLookupMixin
from premium.models import SubscriptionInvoice
from users.models import User

from ..authentication import TokenAuthentication
from ..enums import InvoiceType
from ..exceptions import UnknownInvoiceTypeError
from ..serializers import PremiumInvoiceSerializer

from typing import Any

type Invoice = SubscriptionInvoice
type InvoiceSerializer = PremiumInvoiceSerializer


class InvoiceViewSet(IDLookupMixin, ModelViewSet[Invoice]):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    @cached_property
    def user(self) -> User:
        return get_object_or_404(User, id=self.kwargs['user_id'])

    @cached_property
    def invoice_type(self) -> InvoiceType:
        try:
            return InvoiceType(self.kwargs['invoice_type'])
        except ValueError as error:
            raise NotFound() from error

    def get_queryset(self) -> QuerySet[Invoice]:
        if self.invoice_type == InvoiceType.PREMIUM:
            return self.user.subscription_invoices.all()
        raise UnknownInvoiceTypeError()

    def get_serializer_class(self) -> type[InvoiceSerializer]:
        if self.invoice_type == InvoiceType.PREMIUM:
            return PremiumInvoiceSerializer
        raise UnknownInvoiceTypeError()

    def get_serializer_context(self) -> dict[str, Any]:
        context: dict[str, Any] = super().get_serializer_context()
        context.update({'user': self.user})
        return context
