from django.apps import AppConfig, apps
from django.conf import settings
from django.utils.module_loading import import_string

from collections.abc import Callable
from enum import Enum
from typing import Any

type Endpoint = tuple[str, str, str, Callable[..., Any]]


def filter_public_endpoints(endpoints: list[Endpoint]) -> list[Endpoint]:
    result: list[Endpoint] = []

    for path, path_regex, method, callback in endpoints:
        app_config: AppConfig | None = apps.get_containing_app_config(
            callback.__module__
        )

        if app_config and app_config.name in settings.PUBLIC_APPS:
            result.append((path, path_regex, method, callback))

    return result


def add_x_enum_varnames(result: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
    enum_overrides: dict[str, Any] = getattr(settings, 'SPECTACULAR_SETTINGS', {}).get(
        'ENUM_NAME_OVERRIDES', {}
    )
    schemas: dict[str, Any] = result.get('components', {}).get('schemas', {})

    for schema_name, enum_path in enum_overrides.items():
        if schema_name in schemas:
            try:
                enum_class: Any = import_string(enum_path)
            except ImportError:
                continue

            if issubclass(enum_class, Enum):
                schemas[schema_name]['x-enum-varnames'] = enum_class.__members__.keys()

    return result
