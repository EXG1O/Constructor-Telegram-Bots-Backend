from django.db.models import QuerySet

from rest_framework.decorators import action
from rest_framework.mixins import UpdateModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet

from django_filters.rest_framework import BooleanFilter, DjangoFilterBackend, FilterSet

from constructor_telegram_bots.filters import NumberInFilter
from constructor_telegram_bots.mixins import IDLookupMixin

from ...models import BackgroundTask
from ..authentication import TokenAuthentication
from ..serializers import BackgroundTaskSerializer
from .mixins import TelegramBotMixin

from http import HTTPMethod


class BackgroundTaskFilter(FilterSet):
    ids = NumberInFilter(field_name='id', lookup_expr='in')
    has_source_connections = BooleanFilter(
        field_name='source_connections', method='filter_has_field'
    )

    def filter_has_field(
        self, queryset: QuerySet[BackgroundTask], name: str, value: bool
    ) -> QuerySet[BackgroundTask]:
        return queryset.filter(**{f'{name}__isnull': not value})

    class Meta:
        model = BackgroundTask
        fields = ['has_source_connections']


class BackgroundTaskViewSet(
    IDLookupMixin,
    TelegramBotMixin,
    UpdateModelMixin,
    ReadOnlyModelViewSet[BackgroundTask],
):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = BackgroundTaskSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = BackgroundTaskFilter

    def get_queryset(self) -> QuerySet[BackgroundTask]:
        background_tasks: QuerySet[BackgroundTask] = (
            self.telegram_bot.background_tasks.all()
        )

        if self.action in ['list', 'retrieve']:
            return background_tasks.prefetch_related(
                'source_connections__source_object',
                'source_connections__target_object',
            )

        return background_tasks

    @action(detail=False, methods=[HTTPMethod.PATCH], url_path='update-many')
    def update_many(self, request: Request, telegram_bot_id: int) -> Response:
        serializer = self.get_serializer(
            list(self.filter_queryset(self.get_queryset())),
            data=request.data,
            partial=True,
            many=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
