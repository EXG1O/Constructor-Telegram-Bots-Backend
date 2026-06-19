from django.db.models import QuerySet

from rest_framework.mixins import CreateModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ReadOnlyModelViewSet

from django_filters.rest_framework import DjangoFilterBackend, FilterSet

from constructor_telegram_bots.filters import NumberInFilter
from constructor_telegram_bots.mixins import IDLookupMixin
from constructor_telegram_bots.pagination import LimitOffsetPagination

from ...models import User
from ..authentication import TokenAuthentication
from ..serializers import UserSerializer
from .mixins import TelegramBotMixin


class UserFilter(FilterSet):
    ids = NumberInFilter(field_name='id', lookup_expr='in')
    telegram_ids = NumberInFilter(field_name='telegram_id', lookup_expr='in')

    class Meta:
        model = User
        fields = ['ids', 'telegram_ids']


class UserViewSet(
    IDLookupMixin,
    TelegramBotMixin,
    CreateModelMixin,
    ReadOnlyModelViewSet[User],
):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer
    pagination_class = LimitOffsetPagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = UserFilter

    def get_queryset(self) -> QuerySet[User]:
        return self.telegram_bot.users.all()
