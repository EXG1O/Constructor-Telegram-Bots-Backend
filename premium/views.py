from django.db.models import QuerySet

from rest_framework.decorators import action
from rest_framework.mixins import RetrieveModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet, ReadOnlyModelViewSet

from constructor_telegram_bots.mixins import IDLookupMixin
from users.authentication import JWTAuthentication
from users.models import User
from users.permissions import IsTermsAccepted

from .models import Subscription, SubscriptionInvoice, SubscriptionPrice
from .serializers import (
    SubscriptionInvoiceSerializer,
    SubscriptionPriceSerializer,
    SubscriptionSerializer,
)

from http import HTTPMethod
from typing import cast


class SubscriptionPriceViewSet(IDLookupMixin, ReadOnlyModelViewSet[SubscriptionPrice]):
    authentication_classes = []
    permission_classes = []
    queryset = SubscriptionPrice.objects.all()
    serializer_class = SubscriptionPriceSerializer

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


class SubscriptionViewSet(
    IDLookupMixin, RetrieveModelMixin, GenericViewSet[Subscription]
):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = SubscriptionSerializer

    def get_object(self) -> Subscription:
        return cast(User, self.request.user).subscription
