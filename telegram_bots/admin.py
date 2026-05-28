from django.contrib import admin
from django.db.models import Count
from django.db.models.query import QuerySet
from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _

from constructor_telegram_bots.utils.html import format_html_link

from .models import TelegramBot, User

from typing import Any, Literal


@admin.register(TelegramBot)
class TelegramBotAdmin(admin.ModelAdmin[TelegramBot]):
    search_fields = ['username']
    date_hierarchy = 'added_date'
    list_filter = ['must_be_enabled', 'added_date']
    list_display = [
        'id',
        'owner',
        'username_display',
        'storage_size_display',
        'used_storage_size_display',
        'remaining_storage_size_display',
        'user_count_display',
        'block_count_display',
        'is_private',
        'must_be_enabled',
        'is_enabled_display',
        'added_date',
    ]
    fields = [
        'id',
        'owner',
        'username_display',
        'api_token',
        'storage_size_display',
        'used_storage_size_display',
        'remaining_storage_size_display',
        'user_count_display',
        'block_count_display',
        'is_private',
        'must_be_enabled',
        'is_enabled_display',
        'added_date',
    ]

    def get_queryset(self, request: HttpRequest) -> QuerySet[TelegramBot]:
        return (
            super()
            .get_queryset(request)
            .annotate(
                block_count=(
                    Count('triggers', distinct=True)
                    + Count('messages', distinct=True)
                    + Count('conditions', distinct=True)
                    + Count('background_tasks', distinct=True)
                    + Count('api_requests', distinct=True)
                    + Count('database_operations', distinct=True)
                    + Count('invoices', distinct=True)
                ),
                user_count=Count('users', distinct=True),
            )
        )

    @admin.display(description='@username', ordering='username')
    def username_display(self, telegram_bot: TelegramBot) -> str:
        return format_html_link(
            f'tg://resolve?domain={telegram_bot.username}', f'@{telegram_bot.username}'
        )

    @admin.display(description=_('Размер хранилища'))
    def storage_size_display(self, telegram_bot: TelegramBot) -> str:
        return f'{(telegram_bot.storage_size / 1024**2):.2f}MB'

    @admin.display(description=_('Используемый размер хранилища'))
    def used_storage_size_display(self, telegram_bot: TelegramBot) -> str:
        return f'{(telegram_bot.used_storage_size / 1024**2):.2f}MB'

    @admin.display(description=_('Оставшийся размер хранилища'))
    def remaining_storage_size_display(self, telegram_bot: TelegramBot) -> str:
        return f'{(telegram_bot.remaining_storage_size / 1024**2):.2f}MB'

    @admin.display(description=_('Пользователей'), ordering='user_count')
    def user_count_display(self, telegram_bot: TelegramBot) -> int:
        return telegram_bot.user_count  # type: ignore [attr-defined]

    @admin.display(description=_('Блоков'), ordering='block_count')
    def block_count_display(self, telegram_bot: TelegramBot) -> int:
        return telegram_bot.block_count  # type: ignore [attr-defined]

    @admin.display(description=_('Включен'), boolean=True)
    def is_enabled_display(self, telegram_bot: TelegramBot) -> bool:
        return telegram_bot.is_enabled

    def has_add_permission(self, *args: Any, **kwargs: Any) -> Literal[False]:
        return False

    def has_change_permission(self, *args: Any, **kwargs: Any) -> Literal[False]:
        return False


@admin.register(User)
class UserAdmin(admin.ModelAdmin[User]):
    search_fields = ['telegram_id', 'username', 'first_name', 'last_name']
    date_hierarchy = 'activated_date'
    list_filter = ['is_allowed', 'is_blocked', 'last_activity_date', 'activated_date']
    list_display = [
        'id',
        'telegram_bot',
        'telegram_id',
        'username',
        'first_name',
        'last_name',
        'is_bot',
        'is_premium',
        'is_allowed',
        'is_blocked',
        'last_activity_date',
        'activated_date',
    ]
    fields = [
        'id',
        'telegram_bot',
        'telegram_id',
        'username',
        'first_name',
        'last_name',
        'is_bot',
        'is_premium',
        'is_allowed',
        'is_blocked',
        'last_activity_date',
        'activated_date',
    ]

    def has_add_permission(self, *args: Any, **kwargs: Any) -> Literal[False]:
        return False

    def has_change_permission(self, *args: Any, **kwargs: Any) -> Literal[False]:
        return False
