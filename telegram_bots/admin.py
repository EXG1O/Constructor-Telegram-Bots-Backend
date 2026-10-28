from django.contrib import admin
from django.core.files.storage import default_storage
from django.db.models import Count, IntegerField, Model, OuterRef, Subquery
from django.db.models.functions import Coalesce
from django.db.models.query import QuerySet
from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _

from constructor_telegram_bots.utils.html import format_html_link

from .models import (
    Action,
    APIRequest,
    BackgroundTask,
    Condition,
    DatabaseOperation,
    Invoice,
    Message,
    Randomizer,
    TelegramBot,
    TemporaryVariable,
    Timer,
    Trigger,
    User,
)
from .utils.storage import get_telegram_bot_file_names

from functools import reduce
from typing import Any, Literal
import operator


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

    def _build_count_per_bot_subquery(self, queryset: QuerySet[Model]) -> Coalesce:
        return Coalesce(
            Subquery(
                queryset.filter(telegram_bot=OuterRef('id'))
                .values('telegram_bot')
                .annotate(count=Count('id'))
                .values('count'),
                output_field=IntegerField(),
            ),
            0,
        )

    def get_queryset(self, request: HttpRequest) -> QuerySet[TelegramBot]:
        return (
            super()
            .get_queryset(request)
            .select_related('owner', 'hub')
            .annotate(
                block_count=reduce(
                    operator.add,
                    (
                        self._build_count_per_bot_subquery(model.objects.all())
                        for model in (
                            Trigger,
                            Message,
                            Condition,
                            BackgroundTask,
                            APIRequest,
                            DatabaseOperation,
                            Invoice,
                            TemporaryVariable,
                            Timer,
                            Randomizer,
                            Action,
                        )
                    ),
                ),
                user_count=self._build_count_per_bot_subquery(User.objects.all()),
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

    def delete_model(self, request: HttpRequest, bot: TelegramBot) -> None:
        file_names: set[str] = get_telegram_bot_file_names(telegram_bot=bot)

        super().delete_model(request, bot)

        for file_name in file_names:
            default_storage.delete(file_name)

    def delete_queryset(
        self, request: HttpRequest, queryset: QuerySet[TelegramBot]
    ) -> None:
        file_names: set[str] = set()

        for bot in queryset.iterator():
            file_names.update(get_telegram_bot_file_names(telegram_bot=bot))

        super().delete_queryset(request, queryset)

        for file_name in file_names:
            default_storage.delete(file_name)

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

    def get_queryset(self, request: HttpRequest) -> QuerySet[User]:
        return super().get_queryset(request).select_related('telegram_bot')

    def has_add_permission(self, *args: Any, **kwargs: Any) -> Literal[False]:
        return False

    def has_change_permission(self, *args: Any, **kwargs: Any) -> Literal[False]:
        return False
