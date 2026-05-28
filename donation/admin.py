from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from adminsortable2.admin import SortableAdminMixin
from modeltranslation.admin import TranslationAdmin

from constructor_telegram_bots.utils.html import format_html_link

from .models import Donation, Method, Section


@admin.register(Donation)
class DonationAdmin(admin.ModelAdmin[Donation]):
    date_hierarchy = 'date'
    list_display = ['sum_display', 'sender', 'date']
    fields = ['sum', 'sender', 'date']

    @admin.display(description=_('Сумма'), ordering='sum')
    def sum_display(self, donation: Donation) -> str:
        return f'{donation.sum}€'


@admin.register(Section)
class SectionAdmin(SortableAdminMixin, TranslationAdmin[Section]):
    list_display = ['title', 'position']
    fields = ['title', 'text']


@admin.register(Method)
class MethodAdmin(SortableAdminMixin, admin.ModelAdmin[Method]):
    list_display = ['text', 'link_display', 'value', 'position']
    fields = ['text', 'link', 'value']

    @admin.display(description=_('Ссылка'), ordering='link')
    def link_display(self, method: Method) -> str | None:
        return format_html_link(method.link) if method.link else None
