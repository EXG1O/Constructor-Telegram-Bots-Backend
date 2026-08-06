from rest_framework import serializers

from ..models.base import AbstractBlock, AbstractMedia, AbstractMessageMedia
from .connection import ConnectionSerializer

from typing import Any, Final


class BlockSerializer[T: AbstractBlock](serializers.ModelSerializer[T]):
    class Meta:
        fields = ['id', 'name', 'x', 'y']
        extra_kwargs = {
            'x': {'write_only': True, 'required': False},
            'y': {'write_only': True, 'required': False},
        }

    _UPDATE_FIELDS: Final[tuple[str, ...]] = ('name', 'x', 'y')

    def update(
        self, instance: T, validated_data: dict[str, Any], save: bool = True
    ) -> T:
        instance.name = validated_data.get('name', instance.name)
        instance.x = validated_data.get('x', instance.x)
        instance.y = validated_data.get('y', instance.y)

        if save:
            instance.save(update_fields=self._UPDATE_FIELDS)

        return instance


class DiagramSerializer[T: AbstractBlock](serializers.ModelSerializer[T]):
    source_connections = ConnectionSerializer(many=True, read_only=True)

    class Meta:
        fields = ['id', 'name', 'x', 'y', 'source_connections']
        read_only_fields = ['name']

    _UPDATE_FIELDS: Final[tuple[str, ...]] = ('x', 'y')

    def update(
        self, instance: T, validated_data: dict[str, Any], save: bool = True
    ) -> T:
        instance.x = validated_data.get('x', instance.x)
        instance.y = validated_data.get('y', instance.y)

        if save:
            instance.save(update_fields=self._UPDATE_FIELDS)

        return instance


class MediaSerializer[T: AbstractMedia](serializers.ModelSerializer[T]):
    name = serializers.CharField(
        source='get_original_filename', read_only=True, allow_null=True
    )
    size = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()

    class Meta:
        fields = ['file', 'name', 'size', 'url', 'from_url']
        extra_kwargs = {
            'id': {'read_only': False, 'required': False},
            'file': {
                'write_only': True,
                'required': False,
                'allow_null': True,
            },
        }

    def get_size(self, media: T) -> int | None:
        if not media.file:
            return None
        return media.file.size

    def get_url(self, media: T) -> str | None:
        if not media.file:
            return None
        return media.file.url


class MessageMediaSerializer[T: AbstractMessageMedia](MediaSerializer[T]):
    class Meta(MediaSerializer.Meta):
        fields = MediaSerializer.Meta.fields + ['id', 'position']
