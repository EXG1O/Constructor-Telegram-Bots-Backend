from django.contrib import admin, messages
from django.db.models import F, QuerySet, Sum
from django.http.request import HttpRequest
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from modeltranslation.admin import TranslationAdmin

from platform_bot.models import PlatformBot
from platform_bot.service.models import RefundPayment
from users.models import User

from .enums import InvoiceStatus
from .models import Subscription, SubscriptionInvoice, SubscriptionPrice

from typing import Any, Literal


@admin.register(SubscriptionPrice)
class SubscriptionPriceAdmin(TranslationAdmin[SubscriptionPrice]):
    list_display = [
        'id',
        'badge',
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

    @admin.display(
        description=_('Итоговая сумма в Telegram Stars'),
        ordering=F('amount_stars_per_month') * F('period_months'),
    )
    def amount_stars_display(self, price: SubscriptionPrice) -> str | int:
        return price.amount_stars if price.pk else '-'


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
        self, request: HttpRequest, queryset: QuerySet[SubscriptionInvoice]
    ) -> None:
        updated: int = queryset.update(
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
        self, request: HttpRequest, queryset: QuerySet[SubscriptionInvoice]
    ) -> None:
        updated: int = 0

        for invoice in queryset.exclude(status=InvoiceStatus.PAID).iterator():
            invoice.status = InvoiceStatus.PAID
            invoice.telegram_charge_id = None
            invoice.paid_date = timezone.now()
            invoice.save(update_fields=['status', 'telegram_charge_id', 'paid_date'])
            invoice.activate_subscription()
            updated += 1

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
        self, request: HttpRequest, queryset: QuerySet[SubscriptionInvoice]
    ) -> None:
        queryset = queryset.filter(user__isnull=False, telegram_charge_id__isnull=False)
        updated: int = queryset.update(status=InvoiceStatus.REFUNDED)

        with PlatformBot().get_client() as client:
            client.refund_payments(
                [
                    RefundPayment(
                        user_id=invoice.user.id,
                        user_telegram_id=invoice.user.telegram_id,
                        invoice_id=invoice.id,
                        telegram_charge_id=invoice.telegram_charge_id,
                    )
                    for invoice in queryset.iterator()
                    if invoice.user and invoice.telegram_charge_id
                ]
            )

        self.message_user(
            request,
            message=(
                _(
                    'Выбранные счета (%d) были успешно помечены как возвращённые, '
                    'а звёзды возвращены (%d).'
                )
                % (updated, queryset.aggregate(total=Sum('amount_stars'))['total'] or 0)
            ),
            level=messages.SUCCESS,
        )

    def has_add_permission(self, *args: Any, **kwargs: Any) -> Literal[False]:
        return False


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin[Subscription]):
    date_hierarchy = 'expiry_date'
    search_fields = ['owner__id']
    list_filter = ['expiry_date']
    list_display = ['id', 'owner_id_display', 'expiry_date']
    fields = ['id', 'owner', 'expiry_date']
    readonly_fields = ['id']

    def get_queryset(self, request: HttpRequest) -> QuerySet[Subscription]:
        return super().get_queryset(request).select_related('owner')

    @admin.display(description=_('ID владельца'), ordering='owner__id')
    def owner_id_display(self, subscription: Subscription) -> int:
        return subscription.owner.id
