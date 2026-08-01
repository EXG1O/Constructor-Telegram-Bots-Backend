from django.contrib import admin, messages
from django.db.models import F, QuerySet
from django.http.request import HttpRequest
from django.utils.translation import gettext_lazy as _

from modeltranslation.admin import TranslationAdmin

from users.models import User

from .enums import InvoiceStatus
from .models import Subscription, SubscriptionInvoice, SubscriptionPrice

from typing import Any, Literal


@admin.register(SubscriptionPrice)
class SubscriptionPriceAdmin(TranslationAdmin[SubscriptionPrice]):
    list_display = [
        'id',
        'period_months',
        'amount_stars_per_month',
        'amount_stars_display',
    ]
    fields = [
        'id',
        'badge',
        'period_months',
        'amount_stars_per_month',
        'amount_stars_display',
    ]
    readonly_fields = ['id', 'amount_stars_display']

    def get_queryset(self, request: HttpRequest) -> QuerySet[SubscriptionPrice]:
        return (
            super()
            .get_queryset(request)
            .annotate(
                total_amount_stars=F('amount_stars_per_month') * F('period_months')
            )
        )

    @admin.display(description=_('Цена'), ordering='total_amount_stars')
    def amount_stars_display(self, price: SubscriptionPrice) -> int:
        return price.amount_stars


@admin.register(SubscriptionInvoice)
class SubscriptionInvoiceAdmin(admin.ModelAdmin[SubscriptionInvoice]):
    date_hierarchy = 'created_date'
    search_fields = ['user__id', 'user__telegram_id', 'telegram_charge_id']
    list_filter = ['status', 'created_date', 'paid_date', 'updated_date']
    list_display = [
        'id',
        'user_id_display',
        'status',
        'period_months',
        'amount_stars',
        'telegram_charge_id',
        'created_date',
        'paid_date',
        'updated_date',
    ]
    fields = [
        'id',
        'user',
        'subscription',
        'status',
        'period_months',
        'amount_stars',
        'telegram_charge_id',
        'created_date',
        'paid_date',
        'updated_date',
    ]
    readonly_fields = [
        'id',
        'user',
        'subscription',
        'status',
        'period_months',
        'amount_stars',
        'created_date',
        'paid_date',
        'updated_date',
    ]
    actions = ['make_pending', 'make_paid', 'make_refunded']

    def get_queryset(self, request: HttpRequest) -> QuerySet[SubscriptionInvoice]:
        return super().get_queryset(request).select_related('user')

    @admin.display(description=_('ID пользователя'), ordering='user__id')
    def user_id_display(self, invoice: SubscriptionInvoice) -> int | None:
        user: User | None = invoice.user
        return user.id if user else None

    @admin.action(description=_('Пометить выбранные счета как ожидаемые'))
    def make_pending(
        self, request: HttpRequest, invoices: QuerySet[SubscriptionInvoice]
    ) -> None:
        updated: int = invoices.update(
            subscription=None, status=InvoiceStatus.PENDING, telegram_charge_id=None
        )
        self.message_user(
            request,
            message=(
                _('Выбранные счета (%d) были успешно помечены как ожидаемые.') % updated
            ),
            level=messages.SUCCESS,
        )

    @admin.action(
        description=_('Пометить выбранные счета как оплаченные и активировать подписки')
    )
    def make_paid(
        self, request: HttpRequest, invoices: QuerySet[SubscriptionInvoice]
    ) -> None:
        update_invoices: list[SubscriptionInvoice] = []

        for invoice in invoices:
            invoice.status = InvoiceStatus.PAID
            invoice.telegram_charge_id = None
            invoice.activate_subscription()
            update_invoices.append(invoice)

        updated: int = SubscriptionInvoice.objects.bulk_update(
            update_invoices, fields=['status', 'telegram_charge_id']
        )

        self.message_user(
            request,
            message=(
                _(
                    'Выбранные счета (%d) были успешно помечены как оплаченные, '
                    'а подписки активированы.'
                )
                % updated
            ),
            level=messages.SUCCESS,
        )

    @admin.action(
        description=_('Пометить выбранные счета как возвращённые и вернуть звёзды')
    )
    def make_refunded(
        self, request: HttpRequest, invoices: QuerySet[SubscriptionInvoice]
    ) -> None:
        updated: int = invoices.update(status=InvoiceStatus.REFUNDED)
        self.message_user(
            request,
            message=(
                _(
                    'Выбранные счета (%d) были успешно помечены как возвращённые, '
                    'а звёзды возвращены.'
                )
                % updated
            ),
            level=messages.SUCCESS,
        )

    def has_add_permission(self, *args: Any, **kwargs: Any) -> Literal[False]:
        return False


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin[Subscription]):
    date_hierarchy = 'end_date'
    search_fields = ['owner__id']
    list_filter = ['end_date']
    list_display = ['id', 'owner_id_display', 'end_date']
    fields = ['id', 'owner', 'end_date']
    readonly_fields = ['id']

    def get_queryset(self, request: HttpRequest) -> QuerySet[Subscription]:
        return super().get_queryset(request).select_related('owner')

    @admin.display(description=_('ID владельца'), ordering='owner__id')
    def owner_id_display(self, subscription: Subscription) -> int:
        return subscription.owner.id
