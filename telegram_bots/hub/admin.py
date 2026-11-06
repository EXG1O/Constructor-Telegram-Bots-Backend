from django.contrib import admin
from django.db.models import Count, QuerySet
from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _

from .models import TelegramBotsHub

from typing import Any, Literal


@admin.register(TelegramBotsHub)
class TelegramBotsHubAdmin(admin.ModelAdmin[TelegramBotsHub]):
    search_fields = ['id', 'container_id']
    list_filter = ['is_premium']
    list_display = [
        'id',
        'is_premium',
        'container_id',
        'bot_count_display',
        'idle_start_date',
    ]
    fields = [
        'id',
        'is_premium',
        'container_id',
        'telegram_token',
        'service_token',
        'microservice_token',
        'bot_count_display',
        'idle_start_date',
    ]
    readonly_fields = ['bot_count_display']

    def get_queryset(self, request: HttpRequest) -> QuerySet[TelegramBotsHub]:
        return super().get_queryset(request).annotate(bot_count=Count('bots'))

    @admin.display(description=_('Ботов'), ordering='bot_count')
    def bot_count_display(self, hub: TelegramBotsHub) -> int:
        return hub.bot_count  # type: ignore [attr-defined]

    def has_add_permission(self, *args: Any, **kwargs: Any) -> Literal[False]:
        return False

    def has_change_permission(self, *args: Any, **kwargs: Any) -> Literal[False]:
        return False
