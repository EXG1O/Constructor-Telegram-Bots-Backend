from django.db import models
from django.utils.translation import gettext_lazy as _

from django_stubs_ext.db.models import TypedModelMeta

from .enums import DocumentType


class Document(models.Model):
    type = models.CharField(
        _('Тип'), primary_key=True, max_length=64, choices=DocumentType
    )
    content = models.TextField(_('Содержание'))
    updated_date = models.DateTimeField(_('Обновлён'), auto_now=True)

    class Meta(TypedModelMeta):
        verbose_name = _('Документ')
        verbose_name_plural = _('Документы')

    def __str__(self) -> str:
        return self.type
