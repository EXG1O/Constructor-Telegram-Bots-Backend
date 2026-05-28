from django.contrib import admin

from .models import TelegramBotsHub


@admin.register(TelegramBotsHub)
class TelegramBotsHubAdmin(admin.ModelAdmin[TelegramBotsHub]):
    search_fields = ['id', 'url']
    list_display = ['id', 'url']
    fields = ['id', 'url', 'telegram_token', 'service_token', 'microservice_token']
