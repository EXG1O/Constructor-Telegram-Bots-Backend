from django.db.models import TextChoices
from django.utils.translation import gettext_lazy as _


class DocumentType(TextChoices):
    TERMS_OF_SERVICE = 'terms-of-service', _('Условия использования')
    PRIVACY_POLICY = 'privacy-policy', _('Политика конфиденциальности')
