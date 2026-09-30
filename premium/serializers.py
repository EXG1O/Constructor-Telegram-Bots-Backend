from rest_framework import serializers

from .models import SubscriptionInvoice, SubscriptionPrice


class SubscriptionPriceSerializer(serializers.ModelSerializer[SubscriptionPrice]):
    class Meta:
        model = SubscriptionPrice
        fields = [
            'id',
            'badge',
            'period_months',
            'amount_stars_per_month',
            'amount_stars',
        ]
        read_only_fields = fields


class SubscriptionInvoiceSerializer(serializers.ModelSerializer[SubscriptionInvoice]):
    class Meta:
        model = SubscriptionInvoice
        fields = [
            'id',
            'status',
            'period_months',
            'amount_stars',
            'telegram_charge_id',
            'created_date',
            'paid_date',
        ]
        read_only_fields = fields
