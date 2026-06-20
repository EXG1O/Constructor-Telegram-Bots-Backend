from django.db.models import QuerySet

from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ReadOnlyModelViewSet

from django_filters.rest_framework import (
    BooleanFilter,
    CharFilter,
    DjangoFilterBackend,
    FilterSet,
)

from constructor_telegram_bots.mixins import IDLookupMixin

from ...models import Trigger
from ..authentication import TokenAuthentication
from ..serializers import TriggerSerializer
from .mixins import TelegramBotMixin


class TriggerFilter(FilterSet):
    command = CharFilter(field_name='command__command', lookup_expr='exact')
    command_payload = CharFilter(field_name='command__payload', lookup_expr='exact')
    has_command = BooleanFilter(
        field_name='command__command', method='filter_has_field'
    )
    has_command_payload = BooleanFilter(
        field_name='command__payload', method='filter_has_field'
    )
    has_command_description = BooleanFilter(
        field_name='command__description', method='filter_has_field'
    )
    has_message = BooleanFilter(field_name='message', method='filter_has_field')
    has_message_text = BooleanFilter(
        field_name='message__text', method='filter_has_field'
    )
    has_source_connections = BooleanFilter(
        field_name='source_connections', method='filter_has_field'
    )
    has_target_connections = BooleanFilter(
        field_name='target_connections', method='filter_has_field'
    )

    def filter_has_field(
        self, queryset: QuerySet[Trigger], name: str, value: bool
    ) -> QuerySet[Trigger]:
        queryset = queryset.filter(**{f'{name}__isnull': not value})

        if name in ['source_connections', 'target_connections']:
            queryset = queryset.distinct('id')

        return queryset

    class Meta:
        model = Trigger
        fields = [
            'command',
            'command_payload',
            'has_command_payload',
            'has_message',
            'has_message_text',
            'has_source_connections',
            'has_target_connections',
        ]


class TriggerViewSet(IDLookupMixin, TelegramBotMixin, ReadOnlyModelViewSet[Trigger]):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = TriggerSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = TriggerFilter

    def get_queryset(self) -> QuerySet[Trigger]:
        triggers: QuerySet[Trigger] = self.telegram_bot.triggers.all()

        if self.action in ['list', 'retrieve']:
            return triggers.select_related('command', 'message').prefetch_related(
                'source_connections__source_object',
                'source_connections__target_object',
            )

        return triggers
