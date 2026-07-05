from rest_framework import serializers

from ..models.base import AbstractBlock, AbstractMedia, AbstractMessageMedia
from .connection import ConnectionSerializer

from typing import Any, Final, TypeVar

ABT = TypeVar('ABT', bound=AbstractBlock)
AMT = TypeVar('AMT', bound=AbstractMedia)
AMMT = TypeVar('AMMT', bound=AbstractMessageMedia)


class BlockSerializer(serializers.ModelSerializer[ABT]):
    class Meta:
        fields = ['id', 'name', 'x', 'y']
        extra_kwargs = {
            'x': {'write_only': True, 'required': False},
            'y': {'write_only': True, 'required': False},
        }

    update_fields: Final[list[str]] = ['name', 'x', 'y']

    def update(
        self, instance: ABT, validated_data: dict[str, Any], save: bool = True
    ) -> ABT:
        instance.name = validated_data.get('name', instance.name)
        instance.x = validated_data.get('x', instance.x)
        instance.y = validated_data.get('y', instance.y)

        if save:
            instance.save(update_fields=self.update_fields)

        return instance


class DiagramSerializer(serializers.ModelSerializer[ABT]):
    source_connections = ConnectionSerializer(many=True, read_only=True)

    class Meta:
        fields = ['id', 'name', 'x', 'y', 'source_connections']
        read_only_fields = ['name']

    update_fields: Final[list[str]] = ['x', 'y']

    def update(
        self, instance: ABT, validated_data: dict[str, Any], save: bool = True
    ) -> ABT:
        instance.x = validated_data.get('x', instance.x)
        instance.y = validated_data.get('y', instance.y)

        if save:
            instance.save(update_fields=self.update_fields)

        return instance


class MediaSerializer(serializers.ModelSerializer[AMT]):
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

    def get_size(self, media: AMT) -> int | None:
        if not media.file:
            return None
        return media.file.size

    def get_url(self, media: AMT) -> str | None:
        if not media.file:
            return None
        return media.file.url


class MessageMediaSerializer(MediaSerializer[AMMT]):
    class Meta(MediaSerializer.Meta):
        fields = MediaSerializer.Meta.fields + ['id', 'position']
