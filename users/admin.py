from django.contrib import admin
from django.core.files.storage import default_storage
from django.db.models import Count
from django.db.models.query import QuerySet
from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _

from .models import User
from .utils.storage import get_user_file_names


@admin.register(User)
class UserAdmin(admin.ModelAdmin[User]):
    date_hierarchy = 'joined_date'
    search_fields = ['telegram_id', 'first_name', 'last_name']
    list_filter = [
        'accepted_terms',
        'terms_accepted_date',
        'is_staff',
        'last_login',
        'joined_date',
    ]
    list_display = [
        'id',
        'telegram_id',
        'first_name',
        'last_name',
        'telegram_bot_count',
        'accepted_terms',
        'terms_accepted_date',
        'is_staff',
        'last_login',
        'joined_date',
    ]
    fields = [
        'id',
        'telegram_id',
        'first_name',
        'last_name',
        'telegram_bot_count',
        'groups',
        'accepted_terms',
        'terms_accepted_date',
        'is_staff',
        'last_login',
        'joined_date',
    ]
    readonly_fields = [
        'id',
        'telegram_id',
        'first_name',
        'last_name',
        'telegram_bot_count',
        'accepted_terms',
        'terms_accepted_date',
        'last_login',
        'joined_date',
    ]

    def get_queryset(self, request: HttpRequest) -> QuerySet[User]:
        return (
            super()
            .get_queryset(request)
            .annotate(telegram_bot_count=Count('telegram_bots'))
        )

    def delete_model(self, request: HttpRequest, user: User) -> None:
        file_names: set[str] = get_user_file_names(user)

        super().delete_model(request, user)

        for file_name in file_names:
            default_storage.delete(file_name)

    def delete_queryset(self, request: HttpRequest, queryset: QuerySet[User]) -> None:
        file_names: set[str] = set()

        for user in queryset:
            file_names.update(get_user_file_names(user))

        super().delete_queryset(request, queryset)

        for file_name in file_names:
            default_storage.delete(file_name)

    @admin.display(description=_('Telegram ботов'), ordering='telegram_bot_count')
    def telegram_bot_count(self, user: User) -> int:
        return user.telegram_bots.count()
