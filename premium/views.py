from django.db.models import QuerySet

from rest_framework import serializers, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet

from drf_spectacular.utils import extend_schema, inline_serializer

from constructor_telegram_bots.mixins import IDLookupMixin
from users.authentication import JWTAuthentication
from users.models import User
from users.permissions import IsTermsAccepted

from .models import SubscriptionInvoice, SubscriptionPrice
from .serializers import SubscriptionInvoiceSerializer, SubscriptionPriceSerializer

from http import HTTPMethod
from typing import cast


class SubscriptionPriceViewSet(IDLookupMixin, ReadOnlyModelViewSet[SubscriptionPrice]):
    authentication_classes = []
    permission_classes = []
    queryset = SubscriptionPrice.objects.filter(is_active=True)
    serializer_class = SubscriptionPriceSerializer

    @extend_schema(
        responses={
            status.HTTP_200_OK: inline_serializer(
                name='SubscriptionPriceCheckoutResponse',
                fields={'url': serializers.URLField(read_only=True)},
            )
        }
    )
    @action(
        detail=True,
        methods=[HTTPMethod.GET],
        authentication_classes=[JWTAuthentication],
        permission_classes=[IsAuthenticated & IsTermsAccepted],
    )
    def checkout(self, request: Request, id: int) -> Response:
        return Response(
            {
                'url': self.get_object().get_checkout_url(
                    user_id=cast(User, request.user).id
                )
            }
        )


class SubscriptionInvoiceViewSet(
    IDLookupMixin, ReadOnlyModelViewSet[SubscriptionInvoice]
):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = SubscriptionInvoiceSerializer

    def get_queryset(self) -> QuerySet[SubscriptionInvoice]:
        return cast(User, self.request.user).subscription_invoices.all()
