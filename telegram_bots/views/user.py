from django.db.models import Count, QuerySet
from django.db.models.functions import TruncDate
from django.utils import timezone
from django.utils.translation import gettext as _

from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.mixins import (
    DestroyModelMixin,
    ListModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from django_filters.rest_framework import DjangoFilterBackend

from constructor_telegram_bots.mixins import IDLookupMixin
from constructor_telegram_bots.pagination import LimitOffsetPagination
from constructor_telegram_bots.permissions import ReadOnly
from users.authentication import JWTAuthentication
from users.permissions import IsTermsAccepted

from ..models import User
from ..serializers import UserSerializer
from .mixins import TelegramBotMixin

from datetime import timedelta
from http import HTTPMethod
from typing import Any
import datetime


class UserViewSet(
    IDLookupMixin,
    TelegramBotMixin,
    ListModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
    DestroyModelMixin,
    GenericViewSet[User],
):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated & (IsTermsAccepted | ReadOnly)]
    serializer_class = UserSerializer
    pagination_class = LimitOffsetPagination
    filter_backends = [SearchFilter, DjangoFilterBackend, OrderingFilter]
    search_fields = ['telegram_id', 'username', 'first_name', 'last_name']
    filterset_fields = ['is_allowed', 'is_blocked']
    ordering = ['-id']

    def get_queryset(self) -> QuerySet[User]:
        return self.telegram_bot.users.all()

    @action(detail=False, methods=[HTTPMethod.GET], url_path='timeline-stats')
    def timeline_stats(self, request: Request, telegram_bot_id: int) -> Response:
        field: str = request.query_params.get('field', 'activated_date')

        if field not in ['last_activity_date', 'activated_date']:
            raise ValidationError({'field': _('Недопустимое значение.')})

        try:
            days: int = int(request.query_params.get('days', '7'))
        except ValueError as error:
            raise ValidationError(
                {'days': _('Значение должно быть целым числом.')}
            ) from error

        if days <= 0:
            raise ValidationError(
                {'days': _('Значение должно быть положительным числом.')}
            )
        elif days > 90:
            raise ValidationError({'days': _('Значение должно быть не больше 90.')})

        start_date: datetime.date = timezone.now().date() - timedelta(days=days)
        timeline_data: dict[datetime.date, int] = {
            item['date']: item['count']
            for item in self.get_queryset()
            .filter(**{f'{field}__date__gte': start_date})
            .annotate(date=TruncDate(field))
            .values('date')
            .annotate(count=Count('id'))
        }
        result: list[dict[str, Any]] = []

        for day in range(days + 1):
            date: datetime.date = start_date + timedelta(days=day)
            result.append({'date': date, 'count': timeline_data.get(date, 0)})

        return Response(result)
