from rest_framework import serializers

from .models import Document


class DocumentSerializer(serializers.ModelSerializer[Document]):
    class Meta:
        model = Document
        fields = ['content', 'updated_date']
