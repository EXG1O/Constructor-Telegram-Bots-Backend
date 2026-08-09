from rest_framework import serializers

from ...models import Randomizer
from .connection import ConnectionSerializer


class RandomizerSerializer(serializers.ModelSerializer[Randomizer]):
    source_connections = ConnectionSerializer(many=True)

    class Meta:
        model = Randomizer
        fields = ['id', 'source_connections']
