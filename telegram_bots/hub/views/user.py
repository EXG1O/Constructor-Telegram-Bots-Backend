from django.db.models import QuerySet

from rest_framework.mixins import CreateModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ReadOnlyModelViewSet

from constructor_telegram_bots.mixins import IDLookupMixin
from constructor_telegram_bots.pagination import LimitOffsetPagination

from ...models import User
from ..authentication import TokenAuthentication
from ..serializers import UserSerializer
from .mixins import TelegramBotMixin


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

    def get_queryset(self) -> QuerySet[User]:
        return self.telegram_bot.users.all()
