from django.utils.functional import cached_property

from rest_framework import serializers

from premium.enums import InvoiceStatus
from premium.models import SubscriptionInvoice
from users.models import User

from types import MappingProxyType
from typing import Any, Final, cast


class PremiumInvoiceSerializer(serializers.ModelSerializer[SubscriptionInvoice]):
    _ALLOWED_STATUS_TRANSITIONS: Final[
        MappingProxyType[InvoiceStatus, tuple[InvoiceStatus, ...]]
    ] = MappingProxyType(
        {
            InvoiceStatus.PENDING: (
                InvoiceStatus.PAID,
                InvoiceStatus.FAILED,
                InvoiceStatus.EXPIRED,
            ),
            InvoiceStatus.PAID: (InvoiceStatus.REFUNDED,),
        }
    )

    def __init__(
        self, instance: SubscriptionInvoice | None = None, *args: Any, **kwargs: Any
    ) -> None:
        super().__init__(instance, *args, **kwargs)

        if instance:
            status_field = self.fields['status']
            status_field.read_only = False
            status_field.required = True
        else:
            period_months_field = self.fields['period_months']
            period_months_field.read_only = False
            period_months_field.required = True

            amount_stars_field = self.fields['amount_stars']
            amount_stars_field.read_only = False
            amount_stars_field.required = True

    class Meta:
        model = SubscriptionInvoice
        fields = ['id', 'status', 'period_months', 'amount_stars', 'telegram_charge_id']
        read_only_fields = fields

    @cached_property
    def user(self) -> User:
        user: Any = self.context.get('user')

        if not isinstance(user, User):
            raise TypeError(
                'You not passed a User instance as user to the serializer context.'
            )

        return user

    def to_internal_value(self, data: dict[str, Any]) -> dict[str, Any]:
        if self.instance and data.get('status') == InvoiceStatus.PAID:
            telegram_charge_id_field = self.fields['telegram_charge_id']
            telegram_charge_id_field.read_only = False
            telegram_charge_id_field.required = True

        return super().to_internal_value(data)

    def validate_status(self, value: str) -> str:
        if self.instance and value not in self._ALLOWED_STATUS_TRANSITIONS.get(
            cast(InvoiceStatus, self.instance.status), ()
        ):
            self.fields['status'].fail('invalid_choice', input=value)

        return value

    def validate(self, data: dict[str, Any]) -> dict[str, Any]:
        if (
            data.get('status') == InvoiceStatus.PAID
            and 'telegram_charge_id' not in data
        ):
            raise serializers.ValidationError(
                {
                    'telegram_charge_id': self.fields[
                        'telegram_charge_id'
                    ].error_messages['required']
                },
                code='required',
            )

        return data

    def create(self, validated_data: dict[str, Any]) -> SubscriptionInvoice:
        return self.user.subscription_invoices.create(**validated_data)

    def update(
        self, invoice: SubscriptionInvoice, validated_data: dict[str, Any]
    ) -> SubscriptionInvoice:
        new_status: InvoiceStatus | None = validated_data.get('status')

        if new_status == InvoiceStatus.PAID:
            invoice.activate_subscription(save=False)

        invoice.status = new_status or invoice.status
        invoice.telegram_charge_id = validated_data.get(
            'telegram_charge_id', invoice.telegram_charge_id
        )
        invoice.save(update_fields=['subscription', 'status', 'telegram_charge_id'])

        return invoice
