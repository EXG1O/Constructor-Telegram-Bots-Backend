from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models, transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from django_stubs_ext.db.models import TypedModelMeta

from platform_bot.models import PlatformBot

from .enums import InvoiceStatus

from datetime import datetime, timedelta


class SubscriptionPrice(models.Model):  # type: ignore [django-manager-missing]
    badge = models.CharField(_('Бейдж'), max_length=64, blank=True, null=True)
    period_months = models.PositiveSmallIntegerField(
        _('Период в месяцах'), unique=True, validators=[MinValueValidator(1)]
    )
    amount_stars_per_month = models.PositiveIntegerField(
        _('Сумма в Telegram Stars за месяц'), validators=[MinValueValidator(1)]
    )

    class Meta(TypedModelMeta):
        db_table = 'premium_subscription_price'
        verbose_name = _('Цена подписки')
        verbose_name_plural = _('Цены подписок')
        ordering = ['period_months']

    def __str__(self) -> str:
        return f'{self.amount_stars_per_month}/m ({self.amount_stars}/{self.period_months}m)'

    @property
    def amount_stars(self) -> int:
        return self.amount_stars_per_month * self.period_months

    def get_checkout_url(self, user_id: int) -> str:
        with PlatformBot().get_client() as client:
            return client.init_checkout(
                user_id=user_id,
                title='Premium',
                description=(
                    'Premium subscription for '
                    f'{self.period_months} month{"s" if self.period_months > 1 else ""} '
                    f'({self.period_months * 30} days).'
                ),
                period_months=self.period_months,
                amount=self.amount_stars,
            ).url


class SubscriptionInvoice(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='subscription_invoices',
        verbose_name=_('Пользователь'),
        null=True,
    )
    status = models.CharField(
        _('Статус'), max_length=8, choices=InvoiceStatus, default=InvoiceStatus.PENDING
    )
    period_months = models.PositiveSmallIntegerField(_('Период в месяцах'))
    amount_stars = models.PositiveIntegerField(_('Сумма в Telegram Stars'))
    telegram_charge_id = models.CharField(
        'Telegram Charge ID', max_length=255, null=True, default=None
    )
    created_date = models.DateTimeField(_('Создан'), auto_now_add=True)
    paid_date = models.DateTimeField(_('Оплачен'), null=True, blank=True)
    updated_date = models.DateTimeField(_('Обновлён'), auto_now=True)

    class Meta(TypedModelMeta):
        db_table = 'premium_subscription_invoice'
        verbose_name = _('Счёт за подписку')
        verbose_name_plural = _('Счета за подписки')

    def __str__(self) -> str:
        return f'{self.user}: {self.amount_stars}/{self.period_months}m ({self.status})'

    def activate_subscription(self) -> Subscription:
        current_datetime: datetime = timezone.now()
        period_extension = timedelta(days=self.period_months * 30)
        expiry_date: datetime = current_datetime + period_extension

        with transaction.atomic():
            subscription, created = (
                Subscription.objects.select_for_update().get_or_create(
                    owner=self.user, defaults={'expiry_date': expiry_date}
                )
            )

            if not created:
                if subscription.is_expired:
                    subscription.expiry_date = expiry_date
                else:
                    subscription.expiry_date += period_extension
                subscription.save(update_fields=['expiry_date'])

        return subscription


class Subscription(models.Model):
    owner = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='subscription',
        verbose_name=_('Владелец'),
    )
    expiry_date = models.DateTimeField(_('Истечёт'))

    class Meta(TypedModelMeta):
        db_table = 'premium_subscription'
        verbose_name = _('Подписка')
        verbose_name_plural = _('Подписки')

    def __str__(self) -> str:
        return f'{self.owner}: {self.expiry_date}'

    @property
    def is_expired(self) -> bool:
        return timezone.now() > self.expiry_date
