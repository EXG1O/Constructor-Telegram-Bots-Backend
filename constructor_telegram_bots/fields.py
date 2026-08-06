from django.db import models

from .validators import PublicURLValidator, StrictJSONValidator

from collections.abc import Sequence
from typing import Any, TypeVar

_ST = TypeVar('_ST', contravariant=True)
_GT = TypeVar('_GT', covariant=True)


class PublicURLField(models.URLField[_ST, _GT]):
    default_validators = [PublicURLValidator()]


class StrictJSONField(models.JSONField[_ST, _GT]):
    def __init__(
        self,
        *args: Any,
        max_length: int = 4096,
        allowed_types: tuple[type[dict[Any, Any]] | type[list[Any]], ...] = (
            dict,
            list,
        ),
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.max_length = max_length
        self.allowed_types = allowed_types
        self.validators.append(StrictJSONValidator(max_length, allowed_types))

    def deconstruct(self) -> tuple[str, str, Sequence[Any], dict[str, Any]]:
        name, path, args, kwargs = super().deconstruct()

        if self.max_length == 4096:
            del kwargs['max_length']

        if self.allowed_types != (dict, list):
            kwargs['allowed_types'] = self.allowed_types

        return name, path, args, kwargs
