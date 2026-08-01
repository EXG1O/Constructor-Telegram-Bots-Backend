from django.db.models.enums import TextChoices
from django.utils.translation import gettext_lazy as _


class InvoiceStatus(TextChoices):
    PENDING = 'pending', _('Ожидание')
    PAID = 'paid', _('Оплачено')
    FAILED = 'failed', _('Отклонено')
    EXPIRED = 'expired', _('Истекло')
    REFUNDED = 'refunded', _('Возврат')
