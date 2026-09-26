from rest_framework import serializers

from ...enums import ConnectionObjectType
from ...models import Connection


class ConnectionSerializer(serializers.ModelSerializer[Connection]):
    source_object_type = serializers.ChoiceField(
        choices=ConnectionObjectType.SOURCE_CHOICES
    )
    target_object_type = serializers.ChoiceField(
        choices=ConnectionObjectType.TARGET_CHOICES
    )

    class Meta:
        model = Connection
        fields = [
            'id',
            'source_object_type',
            'source_object_id',
            'target_object_type',
            'target_object_id',
        ]
