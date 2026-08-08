from rest_framework import serializers

from ...models import Timer
from .connection import ConnectionSerializer


class TimerSerializer(serializers.ModelSerializer[Timer]):
    source_connections = ConnectionSerializer(many=True)

    class Meta:
        model = Timer
        fields = ['id', 'duration_seconds', 'source_connections']
