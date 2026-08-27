from django.db.models import QuerySet

from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.mixins import CreateModelMixin, UpdateModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet

from django_filters.rest_framework import CharFilter, DjangoFilterBackend, FilterSet

from constructor_telegram_bots.mixins import IDLookupMixin

from ...models import DatabaseRecord
from ..authentication import TokenAuthentication
from ..serializers import DatabaseRecordSerializer
from .mixins import TelegramBotMixin

from http import HTTPMethod


class DatabaseRecordFilter(FilterSet):
    has_data_path = CharFilter(field_name='data', method='filter_has_data_path')

    def filter_has_data_path(
        self, queryset: QuerySet[DatabaseRecord], name: str, value: str
    ) -> QuerySet[DatabaseRecord]:
        return queryset.filter(**{f'{name}__{value.replace(".", "__")}__isnull': False})

    class Meta:
        model = DatabaseRecord
        fields = ['has_data_path']


class DatabaseRecordViewSet(
    IDLookupMixin,
    TelegramBotMixin,
    CreateModelMixin,
    UpdateModelMixin,
    ReadOnlyModelViewSet[DatabaseRecord],
):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = DatabaseRecordSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = DatabaseRecordFilter
    search_fields = ['data']

    def get_queryset(self) -> QuerySet[DatabaseRecord]:
        return self.telegram_bot.database_records.all()

    @action(
        detail=False, methods=[HTTPMethod.PUT, HTTPMethod.PATCH], url_path='update-many'
    )
    def update_many(self, request: Request, telegram_bot_id: int) -> Response:
        serializer = self.get_serializer(
            list(self.filter_queryset(self.get_queryset())),
            partial=request.method == HTTPMethod.PATCH,
            data=request.data,
            many=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)
