from django.contrib import admin

from .models import Document


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin[Document]):
    list_display = ['type', 'updated_date']
    fields = ['type', 'content', 'updated_date']
    readonly_fields = ['updated_date']
