from rest_framework import serializers

from .models import Section


class SectionSerializer(serializers.ModelSerializer[Section]):
    class Meta:
        model = Section
        fields = ['id', 'title', 'text']
        read_only_fields = fields
