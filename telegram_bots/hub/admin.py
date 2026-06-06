from django.contrib import admin

from .models import TelegramBotsHub

from typing import Any, Literal


@admin.register(TelegramBotsHub)
class TelegramBotsHubAdmin(admin.ModelAdmin[TelegramBotsHub]):
    search_fields = ['id', 'container_id']
    list_display = ['id', 'container_id', 'idle_start_date']
    fields = [
        'id',
        'container_id',
        'telegram_token',
        'service_token',
        'microservice_token',
        'idle_start_date',
    ]

    def has_add_permission(self, *args: Any, **kwargs: Any) -> Literal[False]:
        return False

    def has_change_permission(self, *args: Any, **kwargs: Any) -> Literal[False]:
        return False
