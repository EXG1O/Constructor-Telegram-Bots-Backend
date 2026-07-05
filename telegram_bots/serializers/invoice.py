from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import UploadedFile
from django.db import transaction
from django.db.models.fields.files import FieldFile
from django.utils.translation import gettext as _

from rest_framework import serializers

from ..models import Invoice, InvoiceImage, InvoicePrice
from .base import BlockSerializer, DiagramSerializer, MediaSerializer
from .mixins import TelegramBotMixin

from contextlib import suppress
from typing import TYPE_CHECKING, Any


class InvoiceImageSerializer(MediaSerializer[InvoiceImage]):
    class Meta(MediaSerializer.Meta):
        model = InvoiceImage


class InvoicePriceSerializer(serializers.ModelSerializer[InvoicePrice]):
    class Meta:
        model = InvoicePrice
        fields = ['id', 'label', 'amount']


class InvoiceSerializer(TelegramBotMixin, BlockSerializer[Invoice]):
    image = InvoiceImageSerializer(required=False, allow_null=True)
    prices = InvoicePriceSerializer(many=True)

    class Meta(BlockSerializer.Meta):
        model = Invoice
        fields = BlockSerializer.Meta.fields + [
            'title',
            'description',
            'image',
            'prices',
        ]

    def validate_image(self, data: dict[str, Any] | None) -> dict[str, Any] | None:
        if not data:
            return data

        file: UploadedFile | None = data.get('file')
        has_file: bool = bool(file)
        has_from_url: bool = bool(data.get('from_url'))

        if self.instance and self.partial:
            with suppress(InvoiceImage.DoesNotExist):
                invoice_image = self.instance.image

                if not has_file:
                    has_file = bool(invoice_image.file)
                if not has_from_url:
                    has_from_url = bool(invoice_image.from_url)

        if has_file is has_from_url:
            raise serializers.ValidationError(
                _(
                    'Изображение счёта должно иметь значение только для одного из полей: '
                    "'file' или 'from_url'."
                ),
            )

        file_size: int | None = file.size if file else None

        if file_size and self.telegram_bot.remaining_storage_size - file_size < 0:
            raise serializers.ValidationError(
                _('Превышен лимит хранилища.'), code='max_storage_size_limit'
            )

        return data

    def validate_prices(self, data: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if not ((self.instance and self.partial) or data):
            raise serializers.ValidationError(
                _('Счёт должен содержать хотя бы одну цену.'), code='empty'
            )

        if (
            self.instance.prices.count() + sum('id' not in item for item in data)
            if self.instance and self.partial
            else len(data)
        ) > settings.TELEGRAM_BOT_MAX_INVOICE_PRICES:
            raise serializers.ValidationError(
                _('Нельзя добавлять больше %(max)s цен счёта.')
                % {'max': settings.TELEGRAM_BOT_MAX_INVOICE_PRICES},
                code='max_limit',
            )

        return data

    def validate(self, data: dict[str, Any]) -> dict[str, Any]:
        if (
            not self.instance
            and self.telegram_bot.invoices.count() + 1
            > settings.TELEGRAM_BOT_MAX_INVOICES
        ):
            raise serializers.ValidationError(
                _('Нельзя добавлять больше %(max)s счетов.')
                % {'max': settings.TELEGRAM_BOT_MAX_INVOICES},
                code='max_limit',
            )

        return data

    def create_image(self, invoice: Invoice, data: dict[str, Any]) -> InvoiceImage:
        return InvoiceImage.objects.create(invoice=invoice, **data)

    def create_prices(
        self, invoice: Invoice, data: list[dict[str, Any]]
    ) -> list[InvoicePrice]:
        create_prices: list[InvoicePrice] = []

        for item in data:
            item.pop('id', None)
            create_prices.append(InvoicePrice(invoice=invoice, **item))

        return InvoicePrice.objects.bulk_create(create_prices)

    def create(self, validated_data: dict[str, Any]) -> Invoice:
        image_data: dict[str, Any] | None = validated_data.pop('image', None)
        prices_data: list[dict[str, Any]] | None = validated_data.pop('prices', None)

        image: InvoiceImage | None = None

        try:
            with transaction.atomic():
                invoice: Invoice = self.telegram_bot.invoices.create(**validated_data)

                if image_data:
                    image = self.create_image(invoice, image_data)
                if prices_data:
                    self.create_prices(invoice, prices_data)
        except Exception as error:
            if image and (file := image.file) and (file_name := file.name):
                default_storage.delete(file_name)
            raise error

        return invoice

    def update_image(
        self, invoice: Invoice, data: dict[str, Any] | None
    ) -> InvoiceImage | None:
        if TYPE_CHECKING:
            image: InvoiceImage

        if not data:
            if not self.partial:
                with suppress(InvoiceImage.DoesNotExist):
                    image = invoice.image
                    image.delete()
                    del invoice._state.fields_cache['image']

                    if (file := image.file) and (file_name := file.name):
                        transaction.on_commit(lambda: default_storage.delete(file_name))
            return None

        try:
            image = invoice.image
        except InvoiceImage.DoesNotExist:
            return self.create_image(invoice, data)

        old_file: FieldFile | None = image.file

        image.file = data.get('file')
        image.from_url = data.get('from_url', image.from_url)
        image.save(update_fields=['file', 'from_url'])

        if old_file and (file_name := old_file.name):
            transaction.on_commit(lambda: default_storage.delete(file_name))

        return image

    def update_prices(
        self, invoice: Invoice, data: list[dict[str, Any]] | None
    ) -> list[InvoicePrice] | None:
        if not data:
            if not self.partial:
                invoice.prices.all().delete()
            return None

        create_prices: list[InvoicePrice] = []
        update_prices: list[InvoicePrice] = []

        for item in data:
            try:
                price: InvoicePrice = invoice.prices.get(id=item.pop('id'))
            except KeyError, InvoicePrice.DoesNotExist:
                create_prices.append(InvoicePrice(invoice=invoice, **item))
            else:
                price.label = item.get('label', price.label)
                price.amount = item.get('amount', price.amount)
                update_prices.append(price)

        new_prices: list[InvoicePrice] = InvoicePrice.objects.bulk_create(create_prices)
        InvoicePrice.objects.bulk_update(update_prices, fields=['label', 'amount'])

        prices: list[InvoicePrice] = new_prices + update_prices

        if not self.partial:
            invoice.prices.exclude(id__in=[price.id for price in prices]).delete()

        return prices

    def update(self, invoice: Invoice, validated_data: dict[str, Any]) -> Invoice:  # type: ignore[override]
        image_data: dict[str, Any] | None = validated_data.get('image')
        prices_data: list[dict[str, Any]] | None = validated_data.get('prices')

        image: InvoiceImage | None = None

        try:
            with transaction.atomic():
                super().update(invoice, validated_data, save=False)
                invoice.title = validated_data.get('title', invoice.title)
                invoice.description = validated_data.get(
                    'description', invoice.description
                )
                invoice.save(
                    update_fields=self.update_fields + ['title', 'description']
                )

                image = self.update_image(invoice, image_data)
                self.update_prices(invoice, prices_data)
        except Exception as error:
            if image and (file := image.file) and (file_name := file.name):
                default_storage.delete(file_name)
            raise error

        return invoice


class DiagramInvoiceSerializer(DiagramSerializer[Invoice]):
    class Meta(DiagramSerializer.Meta):
        model = Invoice
